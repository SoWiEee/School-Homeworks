# Java-Course-Example

這個資料夾整理 Java 課堂範例與作業，內容涵蓋物件導向程式設計核心概念：繼承、多型、介面、例外處理前的類別設計、以及小型測驗題實作。

## 目錄結構

- `3.16/`, `4.18/`, `5.24/`, `6.2/`, `6.36/`, `7.21/`, `8.6/`, `9.8/`, `10.8/`, `10.10/`, `10.11/`, `10.13/`, `11.17/`, `11.18/`
  - 以章節/日期為單位的課堂範例與作業
- `Test2Q3_Deck/`, `Test3Q2/`, `Test4Q1/`, `Test4Q2/`, `Test4Q3/`
  - 測驗題練習與解答

## 主題範例

- 員工薪資系統（`Employee`, `SalariedEmployee`, `HourlyEmployee`, `CommissionEmployee`）
- 介面設計（`Payable`, `CarbonFootprint`）
- 幾何類別繼承（`Quadrilateral`, `Rectangle`, `Square`）
- 小型遊戲/角色題（`Warrior`, `Witch`, `Role`）

## 編譯與執行

在單一資料夾內可直接使用：

```bash
javac *.java
java Main
```

若主程式名稱不同，請改成對應 class（例如 `PayrollSystemTest`、`MainTest`）。

## 備註

- 本資料夾偏向課程練習紀錄，程式風格會隨每次作業要求不同。
- 建議使用 JDK 17+（JDK 8 以上通常也可執行大多數範例）。
