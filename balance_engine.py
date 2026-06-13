from decimal import Decimal
from models import db, User, Group, Expense, ExpenseSplit, Settlement

def get_user_balance_drilldown(user_id, group_id):
    """
    Returns a detailed, itemized breakdown of why a user has their balance.
    Rohan's requirement: "show me exactly which expenses make up my balance".
    """
    user = User.query.get(user_id)
    if not user:
        return None
        
    # 1. Expenses Paid by this User (credits to their balance)
    paid_expenses = Expense.query.filter_by(payer_id=user_id, group_id=group_id).all()
    paid_list = []
    total_paid_inr = Decimal('0.00')
    
    for e in paid_expenses:
        inr_val = Decimal(str(e.amount)) * Decimal(str(e.exchange_rate))
        total_paid_inr += inr_val
        paid_list.append({
            "id": e.id,
            "date": e.date.strftime("%Y-%m-%d"),
            "description": e.description,
            "amount": e.amount,
            "currency": e.currency,
            "inr_value": inr_val
        })

    # 2. Expenses Owed by this User (debits to their balance)
    owed_splits = db.session.query(ExpenseSplit, Expense).join(Expense).filter(
        ExpenseSplit.user_id == user_id,
        Expense.group_id == group_id
    ).all()
    
    owed_list = []
    total_owed_inr = Decimal('0.00')
    
    for split, e in owed_splits:
        inr_val = Decimal(str(split.amount_owed)) * Decimal(str(e.exchange_rate))
        total_owed_inr += inr_val
        # Find who paid this expense
        payer_name = e.payer.name
        owed_list.append({
            "expense_id": e.id,
            "date": e.date.strftime("%Y-%m-%d"),
            "description": e.description,
            "paid_by": payer_name,
            "amount_owed": split.amount_owed,
            "currency": e.currency,
            "inr_value": inr_val
        })

    # 3. Settlements Sent by this User (credits - they paid off their debt)
    sent_settlements = Settlement.query.filter_by(sender_id=user_id, group_id=group_id).all()
    sent_list = []
    total_sent_inr = Decimal('0.00')
    
    for s in sent_settlements:
        inr_val = Decimal(str(s.amount)) * Decimal(str(s.exchange_rate))
        total_sent_inr += inr_val
        sent_list.append({
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "receiver": s.receiver.name,
            "amount": s.amount,
            "currency": s.currency,
            "inr_value": inr_val
        })

    # 4. Settlements Received by this User (debits - someone paid them back)
    received_settlements = Settlement.query.filter_by(receiver_id=user_id, group_id=group_id).all()
    received_list = []
    total_received_inr = Decimal('0.00')
    
    for s in received_settlements:
        inr_val = Decimal(str(s.amount)) * Decimal(str(s.exchange_rate))
        total_received_inr += inr_val
        received_list.append({
            "id": s.id,
            "date": s.date.strftime("%Y-%m-%d"),
            "sender": s.sender.name,
            "amount": s.amount,
            "currency": s.currency,
            "inr_value": inr_val
        })

    # Final Net Balance in INR
    # Net Balance = Paid - Owed + Sent - Received
    # E.g., if I paid 1000, and owed 400, my net balance is +600 (the group owes me 600).
    # If I sent a settlement of 200, my balance becomes +800.
    # If I received a settlement of 500, my balance becomes +300.
    net_balance_inr = total_paid_inr - total_owed_inr + total_sent_inr - total_received_inr

    return {
        "user_name": user.name,
        "total_paid_inr": total_paid_inr,
        "total_owed_inr": total_owed_inr,
        "total_sent_inr": total_sent_inr,
        "total_received_inr": total_received_inr,
        "net_balance_inr": net_balance_inr,
        "paid_details": paid_list,
        "owed_details": owed_list,
        "sent_details": sent_list,
        "received_details": received_list
    }

def calculate_group_balances(group_id):
    """
    Calculates the net balance for all users associated with the group in INR.
    Returns a dictionary mapping user names to their net balances.
    """
    group = Group.query.get(group_id)
    if not group:
        return {}
        
    balances = {}
    
    # Get all users who have memberships (or transactions) in the group
    users = User.query.all()
    
    for u in users:
        drilldown = get_user_balance_drilldown(u.id, group_id)
        if drilldown:
            balances[u.name] = drilldown["net_balance_inr"]
            
    return balances

def resolve_group_debts(group_id):
    """
    Aisha's requirement: "I just want one number per person. Who pays whom, how much, done."
    Uses a greedy balance-settlement algorithm to compute the minimum peer-to-peer transfers.
    """
    balances = calculate_group_balances(group_id)
    
    # Filter out users with zero balances (using a small epsilon threshold)
    debtors = [] # (name, balance) where balance is negative
    creditors = [] # (name, balance) where balance is positive
    
    for name, bal in balances.items():
        if bal < Decimal('-0.02'):
            debtors.append({"name": name, "balance": bal})
        elif bal > Decimal('0.02'):
            creditors.append({"name": name, "balance": bal})
            
    # Sort debtors ascending (most negative first)
    debtors.sort(key=lambda x: x["balance"])
    # Sort creditors descending (most positive first)
    creditors.sort(key=lambda x: x["balance"], reverse=True)
    
    transfers = []
    
    d_idx = 0
    c_idx = 0
    
    while d_idx < len(debtors) and c_idx < len(creditors):
        debtor = debtors[d_idx]
        creditor = creditors[c_idx]
        
        debt_amount = -debtor["balance"]
        credit_amount = creditor["balance"]
        
        transfer_amount = min(debt_amount, credit_amount)
        
        # Round transfer amount to 2 decimals
        transfer_amount = transfer_amount.quantize(Decimal('0.01'))
        
        if transfer_amount > 0:
            transfers.append({
                "from": debtor["name"],
                "to": creditor["name"],
                "amount": transfer_amount,
                "currency": "INR"
            })
            
        # Update balances
        debtor["balance"] += transfer_amount
        creditor["balance"] -= transfer_amount
        
        if debtor["balance"] >= Decimal('-0.02'):
            d_idx += 1
        if creditor["balance"] <= Decimal('0.02'):
            c_idx += 1
            
    return transfers
