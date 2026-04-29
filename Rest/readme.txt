Manual:
Should install go complier (https://go.dev/dl/), vscode "go" extension (optional)
Execute: go run main.go
Build: go build main.go (generate main.exe)
Race condition detection (builtin): go run -race main.go (https://go.dev/doc/articles/race_detector)


About the program:
Allocation Logic: tryAllocating()
Lock on SushiBar: sync.Mutex, sync.Cond (Line 38,39)
Create thread: go func()
Default csv is base.csv, should change filename at Line 499

* go (goroutine) 其實可以拿到 thread id，需要引用外部的 GoID 或追蹤 stack
* 感覺 ui 還能優化一下
* 目前都是假設每組客人最多 1 個輪椅
* 之後可能會加入顯示座位利用率及等待時間的功能，方便助教評估