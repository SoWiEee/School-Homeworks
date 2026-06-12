# Rest Simulator Results v2

Recorded on 2026-06-13.

This version keeps the original seating/resource rules and changes only the waiting-queue scheduling policy:

- `maxSkips` is increased from `3` to `1000000`.
- This effectively disables forced-head blocking, so if the queue head cannot currently be seated, later seatable customers may continue to be served.
- Initial resource counts and final test cases are unchanged.

## v2 Final Test Results

| Test Case | v1 Last Seated | v2 Last Seated | Delta | v1 Last Departure | v2 Last Departure | Delta |
|---|---:|---:|---:|---:|---:|---:|
| `test_easy.csv` | 47 | 47 | 0 | 75 | 75 | 0 |
| `test_normal.csv` | 17 | 17 | 0 | 56 | 56 | 0 |
| `test_race_condition.csv` | 10 | 10 | 0 | 33 | 30 | -3 |
| `test_resource_exhaustion.csv` | 251 | 251 | 0 | 999 | 999 | 0 |
| `test_complex.csv` | 108 | 103 | -5 | 999 | 999 | 0 |

## Notes

- The main improvement is `test_complex.csv`: Last Seated improves from `108` to `103`.
- `test_race_condition.csv` keeps the same Last Seated but improves Last Departure from `33` to `30`.
- `test_resource_exhaustion.csv` is bottlenecked by long-lived preloaded customers and limited baby-chair availability, so the final Last Seated remains `251` without changing seating/resource rules.
- The `999` Last Departure values are caused by preloaded customers with `est_dining_time = 999`.
