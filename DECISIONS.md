# DECISIONS.md — Engineering & Product Decision Log

This document tracks all critical engineering and product decisions made during the design and development of the Shared Expenses application.

---

## 1. Backend Tech Stack: Flask vs Django
- **Decision**: **Python Flask**
- **Options Considered**: Python Django, Python Flask.
- **Rationale**: 
  - **Readability**: Flask has minimal boilerplate, meaning there are no hidden configuration layers. Every route, database connection, and query is explicit. This is crucial for the 45-minute live technical session where the developer must defend every line of code.
  - **Speed**: Flask allows building custom endpoints and import logic in under 2 hours without fighting Django's default conventions.
  - **Control**: Building custom splitting models and import validation is simpler in Flask than overriding Django's admin/orm defaults.

---

## 2. Dev Environment Database: SQLite Fallback
- **Decision**: **Dual-Database Support (SQLite for Dev, PostgreSQL for Prod)**
- **Options Considered**:
  - *Option A*: Force PostgreSQL locally by troubleshooting permissions and installing dependencies.
  - *Option B*: Fallback to SQLite locally, using SQLAlchemy's database abstraction.
- **Rationale**:
  - The local system does not have administrator privileges, which prevents launching the Docker Desktop service or installing PostgreSQL via Chocolatey.
  - Using **SQLAlchemy ORM** abstracts the database layers. The application connects using a `DATABASE_URL` environment variable. In local development, it defaults to a local SQLite file (`sqlite:///shared_expenses.db`). When deployed, it switches to PostgreSQL (`postgresql://...`) with **zero code changes**.
  - This guarantees the application is relational-only, meets constraints, and bypasses local privilege limitations.

---

## 3. Handling Mixed Currency (USD/INR)
- **Decision**: **Store original currency and convert to INR at a fixed rate ($1 = ₹83.00)**
- **Options Considered**:
  - *Option A*: Convert on-the-fly and discard USD details.
  - *Option B*: Store original currency and conversion rate, calculate balances in INR.
- **Rationale**:
  - Priya's concern was that "$1 = ₹1" is incorrect. We store the original transaction details (amount and currency) and the exchange rate active at that date.
  - We use a fixed rate of **$1 = ₹83.00** representing the early 2026 exchange rate.
  - The balance summary displays in INR, but users can trace the balance back to the original USD amount.

---

## 4. Membership Date Boundaries & Splits
- **Decision**: **Exclusion & Redistribution**
- **Options Considered**:
  - *Option A*: Fail the import if Meera is billed after March 31st or Sam before mid-April.
  - *Option B*: Remove violating members from the split list and redistribute their shares to the active members of that group on that date.
- **Rationale**:
  - In real-world spreadsheets, people often copy-paste list templates without checking active dates (e.g., Row 36: Meera included in April groceries).
  - Programmatically excluding the inactive member and splitting their portion among active members is the fairest path. It preserves the total amount spent while enforcing membership boundaries.

---

## 5. Settlements Logged as Expenses
- **Decision**: **Auto-promotion to Settlements**
- **Options Considered**:
  - *Option A*: Import them as expenses (which would split them among everyone, causing incorrect balances).
  - *Option B*: Skip/discard them as invalid expenses.
  - *Option C*: Intercept them, skip splitting, and write them directly to the `settlements` table.
- **Rationale**:
  - Transactions like "Rohan paid Aisha back" (Row 14) are payments between individuals.
  - Treating them as expenses splits the amount again, which is incorrect.
  - We detect rows that have empty split types or split with a single user matching the payer and write them to the `settlements` table. This correctly reduces Rohan's debt to Aisha without affecting Priya or Meera.
