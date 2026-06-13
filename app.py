import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from decimal import Decimal
from datetime import datetime
from models import db, User, Group, GroupMembership, Expense, Settlement, ExpenseSplit
from importer import run_import
from balance_engine import calculate_group_balances, resolve_group_debts, get_user_balance_drilldown
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'spreetail_secret_key_shared_expenses'

# Configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///shared_expenses.db')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Helper to check login
def get_logged_in_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.route('/')
def index():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
        
    group = Group.query.filter_by(name="Flat 101").first()
    if not group:
        flash("Database not seeded. Please run seed_db.py first.", "error")
        return "Database not seeded."

    # Fetch memberships for display
    memberships = GroupMembership.query.filter_by(group_id=group.id).all()
    members_info = []
    for m in memberships:
        members_info.append({
            "name": m.user.name,
            "joined_at": m.joined_at.strftime("%Y-%m-%d"),
            "left_at": m.left_at.strftime("%Y-%m-%d") if m.left_at else "Active"
        })

    # Calculate balances and settlements
    balances = calculate_group_balances(group.id)
    settlements_plan = resolve_group_debts(group.id)
    
    # Format balances for templates
    balances_formatted = []
    for name, bal in balances.items():
        balances_formatted.append({
            "name": name,
            "amount": bal,
            "status": "credit" if bal >= 0 else "debt"
        })
        
    # Get all users for settlements dropdown
    users = User.query.all()

    # Get recent settlements list
    recent_settlements = Settlement.query.filter_by(group_id=group.id).order_by(Settlement.date.desc()).all()
    recent_settlements_info = []
    for s in recent_settlements:
        recent_settlements_info.append({
            "date": s.date.strftime("%Y-%m-%d"),
            "sender": s.sender.name,
            "receiver": s.receiver.name,
            "amount": s.amount,
            "currency": s.currency
        })

    # Get recent expenses
    recent_expenses = Expense.query.filter_by(group_id=group.id).order_by(Expense.date.desc()).limit(10).all()
    recent_expenses_info = []
    for e in recent_expenses:
        recent_expenses_info.append({
            "date": e.date.strftime("%Y-%m-%d"),
            "description": e.description,
            "payer": e.payer.name,
            "amount": e.amount,
            "currency": e.currency
        })

    return render_template(
        'index.html',
        current_user=user,
        members=members_info,
        balances=balances_formatted,
        settlements_plan=settlements_plan,
        users=users,
        group=group,
        recent_settlements=recent_settlements_info,
        recent_expenses=recent_expenses_info
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().capitalize()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(name=username).first()
        # For this assignment, we support default password matching for simplicity:
        # User passwords seeded are "username123" (e.g. "aisha123")
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid flatmate name or password.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for('login'))

@app.route('/import', methods=['POST'])
def import_csv():
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    if 'file' not in request.files:
        flash("No file part in upload request.", "error")
        return redirect(url_for('index'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No selected file.", "error")
        return redirect(url_for('index'))
        
    if file:
        # Save temp file
        temp_dir = os.path.join(app.root_path, 'scratch')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, 'uploaded_expenses.csv')
        file.save(temp_path)
        
        try:
            # Re-seed first to have a clean, fresh import for this dataset
            os.system('.venv\\Scripts\\python seed_db.py')
            
            report = run_import(temp_path)
            session['import_report'] = report
            flash("Expenses successfully imported!", "success")
        except Exception as e:
            flash(f"Import failed: {str(e)}", "error")
            
        return redirect(url_for('index'))

@app.route('/settle', methods=['POST'])
def record_settlement():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
        
    group_id = request.form.get('group_id')
    sender_id = request.form.get('sender_id')
    receiver_id = request.form.get('receiver_id')
    amount_str = request.form.get('amount')
    date_str = request.form.get('date')
    
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive.")
            
        settlement_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        settlement = Settlement(
            group_id=int(group_id),
            sender_id=int(sender_id),
            receiver_id=int(receiver_id),
            amount=amount,
            currency='INR',
            exchange_rate=Decimal('1.0000'),
            date=settlement_date
        )
        db.session.add(settlement)
        db.session.commit()
        flash("Settlement successfully recorded!", "success")
    except Exception as e:
        flash(f"Failed to record settlement: {str(e)}", "error")
        
    return redirect(url_for('index'))

@app.route('/trace/<string:name>')
def trace_balance(name):
    user = get_logged_in_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
        
    target_user = User.query.filter_by(name=name).first()
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    group = Group.query.filter_by(name="Flat 101").first()
    drill = get_user_balance_drilldown(target_user.id, group.id)
    
    # Convert Decimals to float for JSON serialization
    drill["total_paid_inr"] = float(drill["total_paid_inr"])
    drill["total_owed_inr"] = float(drill["total_owed_inr"])
    drill["total_sent_inr"] = float(drill["total_sent_inr"])
    drill["total_received_inr"] = float(drill["total_received_inr"])
    drill["net_balance_inr"] = float(drill["net_balance_inr"])
    
    for item in drill["paid_details"]:
        item["amount"] = float(item["amount"])
        item["inr_value"] = float(item["inr_value"])
        
    for item in drill["owed_details"]:
        item["amount_owed"] = float(item["amount_owed"])
        item["inr_value"] = float(item["inr_value"])
        
    for item in drill["sent_details"]:
        item["amount"] = float(item["amount"])
        item["inr_value"] = float(item["inr_value"])
        
    for item in drill["received_details"]:
        item["amount"] = float(item["amount"])
        item["inr_value"] = float(item["inr_value"])
        
    return jsonify(drill)

@app.route('/report')
def view_report():
    user = get_logged_in_user()
    if not user:
        return redirect(url_for('login'))
        
    report = session.get('import_report')
    if not report:
        flash("No import report available. Run an import first.", "info")
        return redirect(url_for('index'))
        
    return render_template('report.html', report=report)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
