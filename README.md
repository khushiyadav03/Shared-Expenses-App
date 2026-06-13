# 💸 Smart Splitwise — Shared Expenses App (Flat 101)

A production-ready, full-stack shared expenses manager built with **Python Flask** and **SQLAlchemy (ORM)**. Designed to ingest a messy CSV export, automatically sanitize and validate data issues, respect changing group memberships over time, track balances in INR/USD, and optimize peer-to-peer settlements using a greedy minimization algorithm.

Ready for instant deployment to **Vercel** with a PostgreSQL production database and SQLite local fallback.

---

## 🚀 Key Features Implemented

1. **Secure Login/Logout**: Fast, session-based authentication. Test credentials for flatmates Aisha, Rohan, Priya, Meera, Sam, and Dev are initialized with passwords matching `[name]123`.
2. **Dynamic Group Membership**: Memberships are time-bounded. Meera left on March 31, 2026, and Sam joined on April 15, 2026. Expenses split only among roommates who were active on the transaction date.
3. **Smarter Currency Support**: USD transactions are converted using a fixed historical exchange rate (1 USD = 83.00 INR). Priya's USD spending is fully traceable.
4. **Comprehensive Splitting**: Handles Equal, Unequal (custom amounts), and Percentage-based splits, scaling percentage allocations automatically if they don't sum to exactly 100%.
5. **No Magic Numbers (Audit Trail)**: Rohan's exact net balance can be fully audited in a click, showing the exact ledger of expenses paid, splits owed, settlements sent, and settlements received.
6. **Optimized Settlements (Greedy Algorithm)**: Aisha gets a simplified "Who pays whom" summary. Reduces transaction counts to the mathematical minimum.
7. **Interactive CSV Importer & Anomaly Detector**:
   - Skips duplicate records and logs them.
   - Converts peer-to-peer transfers logged as expenses (e.g., "Rohan paid Aisha") into direct `Settlement` objects.
   - Cleans formatting, parses flexible dates, rejects out-of-scope splits, and handles negative values.
   - Displays a comprehensive, clean **Import Report** on anomalies.

---

## 🛠️ Local Setup & Installation

### Prerequisites: Python 3.10+
1. **Clone or Navigate to the Workspace Directory**:
   ```bash
   cd "New folder"
   ```
2. **Create and Activate a Virtual Environment**:
   ```bash
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Seed Database and Auto-Import CSV**:
   ```bash
   python seed_db.py
   ```
5. **Run the Development Server**:
   ```bash
   python app.py
   ```
6. Open **`http://127.0.0.1:5000`** in your browser.

---

## 🌐 Deploying to Vercel

The app is fully configured for deployment on **Vercel** via serverless Python functions using the configuration in [vercel.json](vercel.json).

### Steps:
1. Push this workspace directory to a **GitHub** repository.
2. Go to the [Vercel Dashboard](https://vercel.com) and import your repository.
3. **Environment Variables**: Add your live database URL:
   - Key: `DATABASE_URL`
   - Value: `postgresql://<user>:<password>@<host>:<port>/<dbname>` (e.g., Neon, Supabase, or Vercel Postgres).
4. Click **Deploy**.
5. **Zero-Touch Seeding**: On the first page load in production, the app detects that the database is uninitialized and automatically creates all tables and seeds the default group members and initial CSV data!
6. If you ever need to reset the database, click the **Import CSV** button on the dashboard to trigger a full drop, re-creation, and import cycle.

---


## 📂 Codebase Reference & Architecture
- **[app.py](app.py)**: Application entrypoint. Defines routing, session management, file upload paths (using Vercel's writeable `/tmp` environment), and the `@app.before_request` database initialization hook.
- **[models.py](models.py)**: The declarative database schema mapping `User`, `Group`, `GroupMembership`, `Expense`, `ExpenseSplit`, and `Settlement`.
- **[importer.py](importer.py)**: The CSV sanitation engine that parses dates flexibly, detects duplicate entries, maps aliases (e.g. "Mera" -> "Meera"), promotes peer-to-peer transfers to the Settlements table, and computes split balances.
- **[balance_engine.py](balance_engine.py)**: Calculations module. Handles net balance extraction and optimizes debts using a greedy simplification algorithm.
- **[seed_db.py](seed_db.py)**: Relational database seed script. Resets or populates tables with core member schemas and defaults.
- **[templates/](templates/)**: UI templates styled with Vanilla CSS (Glassmorphism layout).
  - `login.html`: Flatmate selection screen.
  - `index.html`: Main dashboard, ledger breakdown, settlements optimizer, and manual transfer form.
  - `report.html`: Detailed post-import validation audit logs.
- **[SCOPE.md](SCOPE.md)**, **[DECISIONS.md](DECISIONS.md)**, **[AI_USAGE.md](AI_USAGE.md)**: Design logs detailing technical tradeoffs, decisions, and AI usage logs.
