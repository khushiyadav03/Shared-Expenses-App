# 📋 CSV Import & Anomaly Detection Report

This report was automatically produced by the app's validation engine when ingesting the messy flatmate spreadsheet export (`Expenses Export.csv`).

## 📊 Summary Metrics

- **Total Rows Processed**: 42
- **Expenses Successfully Imported**: 38
- **Settlements Logged & Promoted**: 2
- **Rows Skipped (Invalid/Critical)**: 2
- **Total Anomalies Detected & Handled**: 22

## 🚨 Detailed Anomaly Log

| Row | Anomaly Type | Severity | Action Taken | Details |
|---|---|---|---|---|
| 7 | Amount Format Issue | LOW | Parsed to decimal | Cleaned amount formatting '1,200' -> 1200. |
| 9 | Payer Name Casing/Alias Mismatch | LOW | Normalized | Normalized payer 'priya' -> 'Priya'. |
| 10 | Float Precision Excess | LOW | Rounded to 2 decimals | Rounded amount '899.995' -> '900.00'. |
| 11 | Payer Name Casing/Alias Mismatch | LOW | Normalized | Normalized payer 'Priya S' -> 'Priya'. |
| 13 | Missing Payer | CRITICAL | Skipped row | Expense 'House cleaning supplies' skipped due to missing payer. |
| 14 | Settlement Logged as Expense | MEDIUM | Imported as peer-to-peer settlement | Auto-promoted direct transfer 'Rohan paid Aisha back' (5000 INR) to Settlements table. |
| 15 | Percentage Split Sum Violation | HIGH | Scaled percentages to sum to 100% | Percentages sum to 110% (expected 100%). Rescaled splits to fit 100%. |
| 20 | USD Transaction Detected | LOW | Applied exchange rate conversion | USD Transaction. Calculated conversion at fixed rate of 1 USD = 83.00 INR. |
| 21 | USD Transaction Detected | LOW | Applied exchange rate conversion | USD Transaction. Calculated conversion at fixed rate of 1 USD = 83.00 INR. |
| 23 | USD Transaction Detected | LOW | Applied exchange rate conversion | USD Transaction. Calculated conversion at fixed rate of 1 USD = 83.00 INR. |
| 23 | Out-of-Scope Split Member | HIGH | Redistributed split among active members | Removed external member 'Dev's friend kabir' from split of 'Parasailing'. |
| 26 | USD Transaction Detected | LOW | Applied exchange rate conversion | USD Transaction. Calculated conversion at fixed rate of 1 USD = 83.00 INR. |
| 27 | Malformed Date | MEDIUM | Normalized | Parsed malformed date 'Mar-14' as '14-03-2026'. |
| 27 | Payer Name Casing/Alias Mismatch | LOW | Normalized | Normalized payer 'rohan ' -> 'Rohan'. |
| 28 | Missing Currency | MEDIUM | Defaulted to INR | Currency was empty. Defaulted to INR. |
| 31 | Zero Amount Expense | MEDIUM | Skipped row | Skipped Swiggy/Double-logged record 'Dinner order Swiggy' as amount is 0. |
| 32 | Percentage Split Sum Violation | HIGH | Scaled percentages to sum to 100% | Percentages sum to 110% (expected 100%). Rescaled splits to fit 100%. |
| 34 | Malformed Date | MEDIUM | Normalized | Normalized swapped date 04-05-2026 -> 05-04-2026 (April 5th) based on notes context. |
| 36 | Membership Inactive Boundary Violation | HIGH | Redistributed split among active members | Excluded 'Meera' from split of 'Groceries BigBasket' on 2026-04-02 because they were not in the group at this date. |
| 38 | Settlement Logged as Expense | MEDIUM | Imported as peer-to-peer settlement | Auto-promoted direct transfer 'Sam deposit share' (15000 INR) to Settlements table. |
| 39 | Membership Inactive Boundary Violation | HIGH | Redistributed split among active members | Excluded 'Sam' from split of 'Housewarming drinks' on 2026-04-10 because they were not in the group at this date. |
| 40 | Membership Inactive Boundary Violation | HIGH | Redistributed split among active members | Excluded 'Sam' from split of 'Electricity Apr' on 2026-04-12 because they were not in the group at this date. |
