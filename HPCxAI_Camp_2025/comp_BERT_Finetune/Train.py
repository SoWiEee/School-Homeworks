import torch
import evaluate
import argparse
import numpy as np
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import TrainingArguments, Trainer, DataCollatorWithPadding
from datasets import load_dataset, ClassLabel
from sklearn.utils.class_weight import compute_class_weight

id2label = {0: "negative", 1: "neutral", 2: "positive"}
label2id = {"negative": 0, "neutral": 1, "positive": 2}


class WeightedLossTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        # 計算加權的 CrossEntropyLoss
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.model.class_weights.to(self.model.device))
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def main(args):
    # load model
    device = "cuda:0" if torch.cuda.is_available() else "cpu"   
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    
    # model = AutoModelForSequenceClassification.from_pretrained(args.model, trust_remote_code=True, num_labels=3,
    #                                                             id2label=id2label, label2id=label2id, low_cpu_mem_usage=True,
    #                                                             device_map=device
    #                                                             )
    # model.to(device)
    # =====================================================================================
    # 修改 1：載入完整的資料集並進行切分
    # 原因：原始腳本只使用 100 筆訓練資料，數量過少，是導致準確率低於 40% 的最主要原因。
    #      使用完整的 27,000+ 筆資料能讓模型充分學習。
    #      同時，我們從訓練集中切分出 10% 作為驗證集，用於在訓練過程中評估模型表現、
    #      防止過擬合，並根據驗證集結果保存最佳模型。
    # =====================================================================================
    print("Loading and splitting the dataset...")
    # 載入完整 'train' split
    full_dataset = load_dataset("mteb/tweet_sentiment_extraction", split="train")
    
    # 將 'label_text' 欄位轉換為 'label' 數字ID
    # 這一步確保資料集的標籤格式符合模型要求
    class_label_feature = ClassLabel(num_classes=len(id2label), names=list(id2label.values()))
    full_dataset = full_dataset.cast_column("label", class_label_feature)
    # full_dataset = full_dataset.map(lambda examples: {"label": label2id[examples["label_text"]]}, remove_columns=["label_text"])

    # 切分資料為 90% 訓練集和 10% 驗證集
    # test_size=0.1 表示 10% 的資料用於驗證
    # stratify_by_column="label" 確保切分後的訓練集和驗證集擁有相同的類別分佈比例，這在處理類別不平衡問題時非常重要。
    train_val_split = full_dataset.train_test_split(test_size=0.1, seed=42, stratify_by_column="label")
    train_dataset = train_val_split["train"]
    eval_dataset = train_val_split["test"]

    print(f"Full dataset loaded.")
    print(f"Training data size: {len(train_dataset)}")
    print(f"Evaluation data size: {len(eval_dataset)}")
    
    # =====================================================================================
    # 新增：計算類別權重
    # 原因：接續上面提到的類別不平衡問題，這裡我們根據訓練集中各類別的實際數量，
    #      計算出對應的權重，並將其附加到模型上，以便自定義的 Trainer 使用。
    # =====================================================================================
    print("Calculating class weights for handling imbalance...")
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(train_dataset["label"]),
        y=np.array(train_dataset["label"])
    )
    # 將 numpy array 轉換為 torch Tensor
    class_weights = torch.tensor(class_weights, dtype=torch.float32)
    print(f"Calculated class weights: {class_weights}")


    # load model
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, trust_remote_code=True, num_labels=3,
        id2label=id2label, label2id=label2id, low_cpu_mem_usage=True,
        device_map=device
    )
    # 將計算好的權重附加到模型物件上，方便 Trainer 調用
    model.class_weights = class_weights
    model.to(device)

    # load dataset
    # train_dataset = load_dataset("mteb/tweet_sentiment_extraction", split="train")
    # print(f"length of dataset is {len(train_dataset)}")

    # small_train_dataset = train_dataset.select([i for i in range(100)])
    # small_eval_dataset = train_dataset.select([i for i in range(100, 110)])

    # # define metrics function
    # metric = evaluate.load("accuracy")


    # preprocess
    def preprocess_data(dataframe):
        return tokenizer(dataframe["text"], truncation=True, max_length=160)
        # return tokenizer(dataframe["text"], max_length=160, padding="max_length", truncation=True)

    print("Preprocessing data...")
    train_dataset = train_dataset.map(preprocess_data, batched=True)
    eval_dataset = eval_dataset.map(preprocess_data, batched=True)

    # 動態填充器
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # 定義評估指標
    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        accuracy = accuracy_metric.compute(predictions=predictions, references=labels)
        f1 = f1_metric.compute(predictions=predictions, references=labels, average="weighted") # 使用 'weighted' F1 分數以考慮類別不平衡
        return {"accuracy": accuracy["accuracy"], "f1": f1["f1"]}

    print("========================")


    # =====================================================================================
    # 修改 3：調整訓練參數 (TrainingArguments)
    # 原因：根據 fine-tuning BERT 的最佳實踐，進行以下調整：
    #      1. learning_rate: 2e-5 是 fine-tuning 時最常用且效果穩定的學習率之一。
    #      2. num_train_epochs: 對於 fine-tuning，2-4 個 epoch 通常足夠。過多 epoch 可能導致過擬合。我們先從 3 開始。
    #      3. per_device_batch_size: 16 或 32 是常見的選擇，這裡使用 16 作為一個內存和速度的平衡點。
    #      4. weight_decay: 加入一個小的權重衰減 (0.01) 作為正則化項，有助於防止過擬合。
    #      5. warmup_ratio: 設置 10% 的訓練步數作為預熱。在訓練初期使用較低的學習率，有助於模型穩定收斂，是訓練 Transformer 的關鍵技巧。
    #      6. evaluation_strategy & save_strategy: 設為 "epoch" 表示每個 epoch 結束後都進行一次評估和儲存。
    #      7. load_best_model_at_end: 確保訓練結束後，Trainer 會載入在驗證集上表現最好的那個模型。
    # =====================================================================================
    training_args = TrainingArguments(
        output_dir=args.output,
        overwrite_output_dir=True,
        # --- 推薦的超參數 ---
        learning_rate=2e-5,
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir="./train_logs",
        logging_strategy="steps",
        logging_steps=100, # 每 100 步輸出一次 log
        fp16=torch.cuda.is_available(), # 如果有 GPU，自動啟用混合精度訓練以加速
        save_total_limit=2, # 只保存最新的 2 個 checkpoints
    )
    # train
    # train_args = TrainingArguments(
    #     # output_dir=args.output,
    #     # overwrite_output_dir=True,
    #     # save_strategy="epoch",
    #     # eval_strategy="epoch",
    #     per_device_train_batch_size=8,
    #     per_device_eval_batch_size=8,
    #     learning_rate=5e-5,
    #     adam_beta1=0.9,
    #     adam_beta2=0.999,
    #     adam_epsilon=1e-8,
    #     num_train_epochs=1,
    #     logging_dir="./train_logs",
    #     load_best_model_at_end=True,
    #     metric_for_best_model="accuracy",
    #     fp16=True
    # )

    # Do not modify or remove this line, this is for us to check your configurations
    # If your submission result doesn't include this, it will be treated as invalid result
    # ================ DO NOT MODIFY OR REMOVE ==============================
    print(f"Training Config: {training_args}")
    # ================ DO NOT MODIFY OR REMOVE ==============================


    # =====================================================================================
    # 修改 4：使用自定義 Trainer 和動態填充器
    # 原因：將前面定義的 WeightedLossTrainer 和 data_collator 應用到訓練流程中。
    # =====================================================================================
    trainer = WeightedLossTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator, # 加入動態填充器
        compute_metrics=compute_metrics,
    )

    print("Start Training...")
    trainer.train()
    trainer.evaluate()


    # After training, list the checkpoint directories to show the output checkpoint number(s)
    print("\nSaved checkpoints in output directory:")
    if os.path.exists(args.output):
        checkpoints = [d for d in os.listdir(args.output) if d.startswith("checkpoint-")]
        checkpoints.sort(key=lambda x: int(x.split("-")[-1]) if x.split("-")[-1].isdigit() else -1)
        for ckpt in checkpoints:
            print(f"  {ckpt}")
    else:
        print("Output directory does not exist.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="google-bert/bert-base-uncased", help="The model name or the path to model's directory.")
    # parser.add_argument("--model", type=str, default="vinai/bertweet-base", ...)
    parser.add_argument("--output", type=str, default="./train_checkpoints", help="Training checkpoints output directory.")

    args = parser.parse_args()

    print(args.model)
    print(args.output)

    main(args)
