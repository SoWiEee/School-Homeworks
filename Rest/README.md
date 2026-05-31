# Dev Test Case

- base.csv
- deadlock.csv
- race.csv
- preoccupied.csv

# Prod Test Case

- test_easy.csv
- test_normal.csv
- test_race_condition.csv
- test_resource_exhaustion.csv
- test_complex.csv

初始值：單人座 14、四人沙發 5、六人沙發 3、嬰兒椅 3、輪椅 2

測資由簡單到困難：
- test_easy.csv (15%)
- test_normal.csv (25%)
- test_race_condition.csv (20%)
- test_resource_exhaustion.csv (20%)
- test_complex.csv (10%)
- 進階功能如家庭降級、輸出內容展示等 (10%)

Baseline（FIFO）：
Test Case					| Last Seated	| Last Departure (Time)
-----------------------------------------------------------------------------------
test_easy.csv					| 47			| 75
test_normal.csv				| 34			| 63
test_race_condition.csv			| 28			| 51
test_resource_exhaustion.csv	| 548		| 999
test_complex.csv				| 248		| 999


