# Rest Simulator Results v1

Recorded on 2026-06-13.

This file records the current `sushi_safe.cpp` result before further scheduling optimizations. These numbers are the baseline for comparing later versions.

## Build And Run

```powershell
cd Rest
g++ -std=c++17 -O2 -pthread sushi_safe.cpp -o sushi_safe.exe
.\sushi_safe.exe final_test\<case>.csv
```

`Last Seated` is the maximum timestamp among `seated` events.
`Last Departure` is the maximum timestamp among `release` events.

## v1 Final Test Results

| Test Case | Last Seated | Last Departure | Output Lines |
|---|---:|---:|---:|
| `test_easy.csv` | 47 | 75 | 20 |
| `test_normal.csv` | 17 | 56 | 36 |
| `test_race_condition.csv` | 10 | 33 | 45 |
| `test_resource_exhaustion.csv` | 251 | 999 | 47 |
| `test_complex.csv` | 108 | 999 | 87 |

## Notes

- `test_easy.csv` matches the older FIFO baseline for Last Seated / Last Departure.
- `test_normal.csv`, `test_race_condition.csv`, `test_resource_exhaustion.csv`, and `test_complex.csv` already improve Last Seated compared with the older FIFO notes in `README.md`.
- The `999` Last Departure values come from preloaded customers with `est_dining_time = 999`, so they are not necessarily improvable unless the assignment allows changing how preoccupied customers are counted or seated.
- The largest remaining Last Seated bottlenecks are `test_resource_exhaustion.csv` and `test_complex.csv`.
