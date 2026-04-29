%[text] # Task C: 失敗案例分析與改善
%[text] 針對 P02 演講廳場景，示範 CLAHE（Task B 採用方法）與 Global HE 在高動態範圍場景下的失敗現象，並以 Gamma 校正與收緊 ClipLimit 的 CLAHE 作為改善方案。量化指標：Mean、Std、高光截斷比（HCR，≥240 像素佔比）、亮部局部 Std（原始 V>0.65 遮罩內的灰階 Std）。
%%
%[text] ## 建立輸出資料夾
if ~exist('output/task_c', 'dir'); mkdir('output/task_c'); end
%%
%[text] ## 載入 P02 與定義量化遮罩
img  = imread('assets/P02.jpg');
gray = rgb2gray(img);
hsv0 = rgb2hsv(img);
% 亮部遮罩：以原始 V 通道 > 0.65 界定「簡報投影區域」
bright_mask = hsv0(:,:,3) > 0.65;
%%
%[text] ## 各方法影像生成與指標計算
% --- 原始 ---
g0    = double(gray);
mn0   = mean(g0(:));   sd0   = std(g0(:));
hcr0  = sum(g0(:)>=240)/numel(g0)*100;
lsd0  = std(g0(bright_mask));
% --- Global HE（失敗方法 A）---
hsv_ghe        = hsv0;
hsv_ghe(:,:,3) = histeq(hsv0(:,:,3));
img_ghe  = im2uint8(hsv2rgb(hsv_ghe));
g_ghe    = double(rgb2gray(img_ghe));
mn_ghe   = mean(g_ghe(:));   sd_ghe  = std(g_ghe(:));
hcr_ghe  = sum(g_ghe(:)>=240)/numel(g_ghe)*100;
lsd_ghe  = std(g_ghe(bright_mask));
% --- CLAHE ClipLimit=0.02（Task B 採用，但在亮部細線上失敗）---
hsv_cl        = hsv0;
hsv_cl(:,:,3) = adapthisteq(hsv0(:,:,3),'ClipLimit',0.02,'NumTiles',[8 8]);
img_cl  = im2uint8(hsv2rgb(hsv_cl));
g_cl    = double(rgb2gray(img_cl));
mn_cl   = mean(g_cl(:));   sd_cl  = std(g_cl(:));
hcr_cl  = sum(g_cl(:)>=240)/numel(g_cl)*100;
lsd_cl  = std(g_cl(bright_mask));
% --- Gamma γ=0.6，套用於 HSV V 通道（改善方案 A）---
hsv_ga        = hsv0;
hsv_ga(:,:,3) = hsv0(:,:,3).^0.6;
img_ga  = im2uint8(hsv2rgb(hsv_ga));
g_ga    = double(rgb2gray(img_ga));
mn_ga   = mean(g_ga(:));   sd_ga  = std(g_ga(:));
hcr_ga  = sum(g_ga(:)>=240)/numel(g_ga)*100;
lsd_ga  = std(g_ga(bright_mask));
% --- CLAHE ClipLimit=0.005，NumTiles=[16 16]（改善方案 B）---
hsv_cl2        = hsv0;
hsv_cl2(:,:,3) = adapthisteq(hsv0(:,:,3),'ClipLimit',0.005,'NumTiles',[16 16]);
img_cl2  = im2uint8(hsv2rgb(hsv_cl2));
g_cl2    = double(rgb2gray(img_cl2));
mn_cl2   = mean(g_cl2(:));   sd_cl2  = std(g_cl2(:));
hcr_cl2  = sum(g_cl2(:)>=240)/numel(g_cl2)*100;
lsd_cl2  = std(g_cl2(bright_mask));
%%
%[text] ## 統計輸出
fprintf('=== P02 失敗案例分析 ===\n');
fprintf('%-26s  Mean   Std   HCR%%  LocalStd\n', '方法');
fprintf('%-26s  %5.1f  %5.1f  %4.1f  %6.1f\n', '原始',               mn0,    sd0,    hcr0,    lsd0);
fprintf('%-26s  %5.1f  %5.1f  %4.1f  %6.1f\n', 'Global HE [失敗A]',  mn_ghe, sd_ghe, hcr_ghe, lsd_ghe);
fprintf('%-26s  %5.1f  %5.1f  %4.1f  %6.1f\n', 'CLAHE 0.02 [失敗B]', mn_cl,  sd_cl,  hcr_cl,  lsd_cl);
fprintf('%-26s  %5.1f  %5.1f  %4.1f  %6.1f\n', 'Gamma 0.6 [改善A]',  mn_ga,  sd_ga,  hcr_ga,  lsd_ga);
fprintf('%-26s  %5.1f  %5.1f  %4.1f  %6.1f\n', 'CLAHE 0.005 [改善B]',mn_cl2, sd_cl2, hcr_cl2, lsd_cl2);
%%
%[text] ## 視覺比較圖（上排：影像，下排：灰階直方圖）
tiledlayout(2,5,'TileSpacing','compact','Padding','compact')
nexttile; imshow(img);     title(sprintf('原始\nM=%.0f HCR=%.1f%%',                   mn0,    hcr0))
nexttile; imshow(img_ghe); title(sprintf('Global HE [失敗A]\nM=%.0f HCR=%.1f%%',      mn_ghe, hcr_ghe))
nexttile; imshow(img_cl);  title(sprintf('CLAHE 0.02 [失敗B]\nM=%.0f HCR=%.1f%%',     mn_cl,  hcr_cl))
nexttile; imshow(img_ga);  title(sprintf('Gamma \\gamma=0.6 [改善A]\nM=%.0f HCR=%.1f%%', mn_ga,  hcr_ga))
nexttile; imshow(img_cl2); title(sprintf('CLAHE 0.005 [改善B]\nM=%.0f HCR=%.1f%%',    mn_cl2, hcr_cl2))
nexttile; histogram(g0(:),    128,'BinLimits',[0,255]); xlabel('像素值'); ylabel('數量')
nexttile; histogram(g_ghe(:), 128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(g_cl(:),  128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(g_ga(:),  128,'BinLimits',[0,255]); xlabel('像素值')
nexttile; histogram(g_cl2(:), 128,'BinLimits',[0,255]); xlabel('像素值')
saveas(gcf,'output/task_c/comparison.png')
%%
%[text] ## 匯出各方法處理結果
imwrite(img,     'output/task_c/c1-orig.png')
imwrite(img_ghe, 'output/task_c/c2-ghe_fail.png')
imwrite(img_cl,  'output/task_c/c3-clahe_fail.png')
imwrite(img_ga,  'output/task_c/c4-gamma_improve.png')
imwrite(img_cl2, 'output/task_c/c5-clahe_improve.png')
%[text]

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
