# AI_USAGE.md — AI Collaboration Log

This document logs the AI tools used, key prompts, and three concrete cases where the AI assistant generated incorrect code, how it was caught, and what was changed to fix it.

---

## 1. AI Tools Used
- **Primary AI Collaborator**: Antigravity (powered by Gemini models).
- **Environment**: Sandboxed terminal workspace with python/pip execution.

---

## 2. Key Prompts Used
1. *"Propose a 2-hour build plan: tech stack overview (Python Flask/Django + PostgreSQL), database schema outline, phased approach to features..."*
2. *"yes proceed further and make this whole project"*
3. *"recheck the folder now i have updated the file"*

---

## 3. Concrete Cases of AI Errors & Corrections

### Case 1: Parenthesis Placement in Float Precision Condition (`importer.py`)
- **What the AI produced**:
  ```python
  if len(str(amount).split('.') > 1 and len(str(amount).split('.')[1])) > 2:
  ```
- **How it was caught**:
  Running the `test_import.py` runner script failed with the following traceback:
  `TypeError: '>' not supported between instances of 'list' and 'int'`
- **What was changed**:
  The parenthesis were closed too late (checking if the split list was `> 1` inside the `len()` function). It was corrected to:
  ```python
  if len(str(amount).split('.')) > 1 and len(str(amount).split('.')[1]) > 2:
  ```

### Case 2: Windows Console Unicode Encoding Crash (`test_balances.py`)
- **What the AI produced**:
  Standard print formatting using the Rupee Unicode symbol:
  ```python
  print(f"{name:<10}: \u20b9{bal:,.2f}")
  ```
- **How it was caught**:
  Executing the `test_balances.py` script on Windows PowerShell crashed with:
  `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9' in position 12: character maps to <undefined>`
- **What was changed**:
  Windows terminal encoding is often set to `cp1252` by default. We modified the output formatting to print `Rs.` instead of the Unicode `₹` symbol to ensure the script executes cleanly on all developer consoles.

### Case 3: Initial Missing Payer Handling Check
- **What the AI produced**:
  Initially, the CSV parser skipped missing payer check rows but didn't register them as critical skips, which would have allowed splits with an empty string as a name.
- **How it was caught**:
  During design validation of the column structure in `Expenses Export.csv` (specifically Row 13, where payer was blank), we realized that an empty string would lead to integrity check failures in the database splits table (as there is no user named `""`).
- **What was changed**:
  We added a validation rule at the beginning of row parsing that flags empty `paid_by` rows as a `critical` severity anomaly and skips the row immediately, preventing database constraint violation crashes.
