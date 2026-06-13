import os
from flask import Flask
from models import db, User, Group
from balance_engine import calculate_group_balances, resolve_group_debts, get_user_balance_drilldown

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shared_expenses.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    group = Group.query.filter_by(name="Flat 101").first()
    if not group:
        print("Please run seed_db.py and test_import.py first!")
        exit(1)
        
    print("=== NET BALANCES ===")
    balances = calculate_group_balances(group.id)
    for name, bal in balances.items():
        print(f"{name:<10}: Rs. {bal:,.2f}")
        
    print("\n=== AISHA'S SETTLEMENT PLAN (Who pays whom) ===")
    transfers = resolve_group_debts(group.id)
    for t in transfers:
        print(f"{t['from']} pays {t['to']} -> Rs. {t['amount']:,.2f}")
        
    print("\n=== ROHAN'S BALANCE DRILLDOWN (Traceability) ===")
    rohan_user = User.query.filter_by(name="Rohan").first()
    if rohan_user:
        drill = get_user_balance_drilldown(rohan_user.id, group.id)
        print(f"Rohan's Net Balance: Rs. {drill['net_balance_inr']:,.2f}")
        print(f"  Total Paid:  Rs. {drill['total_paid_inr']:,.2f}")
        print(f"  Total Owed:  Rs. {drill['total_owed_inr']:,.2f}")
        print(f"  Total Sent:  Rs. {drill['total_sent_inr']:,.2f}")
        print(f"  Total Recvd: Rs. {drill['total_received_inr']:,.2f}")
        
        print("\n  Expenses Paid by Rohan:")
        for e in drill['paid_details']:
            print(f"    - {e['date']} | {e['description']:<25} | {e['amount']} {e['currency']} (Rs. {e['inr_value']:,.2f})")
            
        print("\n  Expenses Owed by Rohan (in splits):")
        for e in drill['owed_details']:
            print(f"    - {e['date']} | {e['description']:<25} | Paid by: {e['paid_by']:<6} | Owed: {e['amount_owed']} {e['currency']} (Rs. {e['inr_value']:,.2f})")
            
        print("\n  Settlements Sent by Rohan:")
        for s in drill['sent_details']:
            print(f"    - {s['date']} | Paid to: {s['receiver']:<6} | amount: {s['amount']} {s['currency']} (Rs. {s['inr_value']:,.2f})")

        print("\n  Settlements Received by Rohan:")
        for s in drill['received_details']:
            print(f"    - {s['date']} | Recvd from: {s['sender']:<6} | amount: {s['amount']} {s['currency']} (Rs. {s['inr_value']:,.2f})")
