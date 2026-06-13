import os
from flask import Flask
from models import db
from importer import run_import

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shared_expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    csv_path = "Expenses Export.csv"
    print(f"Running import on: {csv_path}")
    try:
        report = run_import(csv_path)
        print("\n=== IMPORT REPORT SUMMARY ===")
        print(f"Total Rows Processed: {report['total_rows_processed']}")
        print(f"Expenses Imported:   {report['expenses_imported']}")
        print(f"Settlements Imported: {report['settlements_imported']}")
        print(f"Rows Skipped:        {report['rows_skipped']}")
        print(f"Anomalies Detected:  {len(report['anomalies'])}")
        
        print("\n=== DETAILED ANOMALY LOG ===")
        for a in report['anomalies']:
            print(f"Row {a['row']:<3} | {a['type']:<35} | {a['severity'].upper():<8} | Action: {a['action']}")
            print(f"        Details: {a['details']}")
            print("-" * 80)
            
    except Exception as e:
        print("Import failed with error:", e)
