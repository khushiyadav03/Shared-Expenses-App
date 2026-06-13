# SCOPE.md — Anomaly Log & Database Schema

This document logs every data anomaly detected in `Expenses Export.csv` and details our policy for handling each one. It also outlines our relational database schema.

---

## 1. CSV Data Anomaly Log

Below is the list of anomalies detected in `Expenses Export.csv` and the programmatic policies applied by the importer:

| # | Anomaly Type | Row/Line | CSV Raw Data | Policy Applied (Action taken) |
|---|---|---|---|---|
| **1** | **Duplicate Entries (Case-Insensitive)** | 5 & 6 | `08-02-2026,Dinner at Marina Bites,Dev,3200,INR` vs `08-02-2026,dinner - marina bites,Dev,3200,INR` | **De-duplicate**: Compare case-insensitive description, date, payer, amount, and splits. Skip the second row and log it. |
| **2** | **Potential Duplicate (Payer/Amount Conflict)** | 24 & 25 | `11-03-2026,Dinner at Thalassa,Aisha,2400` vs `11-03-2026,Thalassa dinner,Rohan,2450` | **Log & Import Both**: Notes say Aisha's is wrong, but since payer and amounts differ, import both and surface a warning for manual reconciliation. |
| **3** | **Number Formatting (Quotes & Comma)** | 7 | `10-02-2026,Electricity Feb,Aisha,"1,200",INR` | **Clean & Parse**: Strip quotes and commas, convert to numeric `1200.00`. Log a warning. |
| **4** | **Payer Name Case Mismatch** | 9 | `14-02-2026,Movie night snacks,priya,640,INR` | **Normalize Payer**: Map `priya` to capitalized `Priya`. Log the normalization. |
| **5** | **Incorrect Float Precision** | 10 | `15-02-2026,Cylinder refill,Rohan,899.995,INR` | **Round Amount**: Round to 2 decimal places (`900.00`). Log the rounding action. |
| **6** | **Misspelled / Suffix Name** | 11 | `18-02-2026,Groceries DMart,Priya S,1875,INR` | **Normalize Payer**: Map `Priya S` to standard group member `Priya`. Log the mapping. |
| **7** | **Missing Payer (Blank)** | 13 | `22-02-2026,House cleaning supplies,,780,INR` | **Validation Failure**: Since the payer is unknown, skip the row and log as a critical error (requires manual correction). |
| **8** | **Settlement Logged as Expense** | 14 & 38 | `25-02-2026,Rohan paid Aisha back,Rohan,5000` & `08-04-2026,Sam deposit share,Sam,15000` | **Parse as Settlement**: Intercept these records (empty split_type, split_with is single user). Store them in the `settlements` table rather than `expenses`. |
| **9** | **Percentage Split Sum > 100%** | 15 & 32 | `...percentage,Aisha;Rohan;Priya;Meera,Aisha 30%; Rohan 30%; Priya 30%; Meera 20%` (Sum = 110%) | **Normalize Splits**: Scale splits proportionally so they sum to 100% (e.g. divide each by 1.1). Log a warning. |
| **10** | **USD Currency Mixing** | 20, 21, 23, 26 | `Goa villa booking,Dev,540,USD` | **Explicit Currency Conversion**: Store transactions in original currency but convert to INR using a fixed exchange rate of **$1 = ₹83.00** for balance calculations. |
| **11** | **Out-of-Scope Split Member** | 23 | `...equal,Aisha;Rohan;Priya;Dev;Dev's friend Kabir` | **Filter Split**: Remove external non-group members (`Dev's friend Kabir`) and redistribute their split share among active group members. Log warning. |
| **12** | **Negative Amount (Refund)** | 26 | `12-03-2026,Parasailing refund,Dev,-30,USD` | **Process Refund**: Treat negative amounts as valid refunds. Subtract them from the amount owed by split members. |
| **13** | **Malformed Date String** | 27 | `Mar-14,Airport cab,rohan` | **Parse Date**: Parse `Mar-14` (interpreted as March 14, 2026) and normalize to standard `%Y-%m-%d`. |
| **14** | **Missing Currency** | 28 | `15-03-2026,Groceries DMart,Priya,2105,,equal...` | **Fallback Currency**: Default missing currency to `INR`. Log warning. |
| **15** | **Zero Amount Expense** | 31 | `22-03-2026,Dinner order Swiggy,Priya,0,INR` | **Skip Expense**: Ignore zero-amount entries. Log warning. |
| **16** | **Membership Scope Violation** | 36 | `02-04-2026,Groceries,Priya,2640,equal,Aisha;Rohan;Priya;Meera` | **Enforce Member Bounds**: Meera left March 31st. Exclude Meera from splits dated after her departure. Redistribute her share to active members. Log warning. |

---

## 2. Database Schema (PostgreSQL)

```sql
-- Core users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group memberships with join/leave bounds
CREATE TABLE group_memberships (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at DATE NOT NULL,
    left_at DATE, -- NULL if currently active
    CONSTRAINT unique_membership UNIQUE(group_id, user_id)
);

-- Shared expenses
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    payer_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    description VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR', -- 'USD' or 'INR'
    exchange_rate DECIMAL(10, 4) NOT NULL DEFAULT 1.0000, -- Rate to convert to INR
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense splits
CREATE TABLE expense_splits (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount_owed DECIMAL(12, 2) NOT NULL,
    split_ratio DECIMAL(10, 4), -- percentage or share coefficient
    CONSTRAINT unique_expense_user_split UNIQUE(expense_id, user_id)
);

-- Debt settlements/transfers
CREATE TABLE settlements (
    id SERIAL PRIMARY KEY,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    exchange_rate DECIMAL(10, 4) NOT NULL DEFAULT 1.0000,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
