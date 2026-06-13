# Shared Expenses App — Flat 101

A full-stack shared expenses application built with **Python Flask** and **SQLAlchemy** (ORM relational database). The app handles membership join/leave dates, currency conversion (USD/INR), peer-to-peer settlements, and detailed balance traceability.

It includes an anomaly detection CSV import engine that parses, sanitizes, and normalizes a messy spreadsheet export (`Expenses Export.csv`), resolving 16 distinct data issues without crashing.

---

## 🚀 Live Demo & Deployment
- **Local Dev Server**: `http://127.0.0.1:5000`
- **Database**: Relational SQLite (Local dev fallback) / PostgreSQL (Production)

---

## 🛠️ Local Setup & Installation

### Prerequisite: Python 3.10+
1. **Clone/Open the project directory**:
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
4. **Initialize and Seed the Database**:
   This resets the tables, seeds the flatmates, registers their membership dates (Meera active Feb-March, Sam active from mid-April), and automatically imports `Expenses Export.csv`.
   ```bash
   python seed_db.py
   ```
5. **Run the Server**:
   ```bash
   python app.py
   ```
6. Open your browser to **`http://127.0.0.1:5000`**.

---

## 🌐 Deploying to Vercel

The application is fully pre-configured for serverless deployment on **Vercel** via `vercel.json`.

### Steps:
1. Push this project folder to a **GitHub** repository.
2. Go to [Vercel Dashboard](https://vercel.com) and click **Add New Project**.
3. Import your GitHub repository.
4. **Environment Variables**: Add your production database connection string under Environment Variables:
   - Key: `DATABASE_URL`
   - Value: `postgresql://<user>:<password>@<host>:<port>/<dbname>` (e.g. from Neon.tech, Supabase, or Vercel Postgres).
5. Click **Deploy**. Vercel will install dependencies from `requirements.txt` and route all serverless functions to `app.py`.

---

## 📑 Core Files Log
- **[SCOPE.md](SCOPE.md)**: Anomaly resolution log mapping the 16 CSV data errors and full database schema logic.
- **[DECISIONS.md](DECISIONS.md)**: Product and engineering choices log (Flask selection, currency conversion policies, SQLite local fallback database design).
- **[AI_USAGE.md](AI_USAGE.md)**: Logs the AI prompts used, tool integrations, and three code errors identified and resolved.

---

## 💡 Flatmate Credentials (Seeded Login)
Log in as any flatmate to test their view. Seeding passwords follow the pattern: **`[name]123`** (lowercase):
- **Aisha**: `aisha123`
- **Rohan**: `rohan123`
- **Priya**: `priya123`
- **Meera**: `meera123`
- **Sam**: `sam123`
- **Dev**: `dev123`

---

## 🤖 AI Assistance
- **AI Tool**: Antigravity AI (Google DeepMind Team, powered by Gemini 3.5 models).
