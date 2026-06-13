import csv
import os
import re
from datetime import datetime, date
from decimal import Decimal
from models import db, User, Group, GroupMembership, Expense, ExpenseSplit, Settlement

# Fixed Exchange Rate for USD -> INR
USD_TO_INR_RATE = Decimal('83.00')

def clean_amount(amount_str):
    """Clean quotes and commas from amount strings and return Decimal."""
    if not amount_str:
        return Decimal('0.00')
    cleaned = amount_str.replace('"', '').replace(',', '').strip()
    return Decimal(cleaned)

def parse_date_flexible(date_str, notes=""):
    """Parse dates with multiple fallback formats and apply custom rules."""
    date_str = date_str.strip()
    
    # Custom rule for Row 34 "04-05-2026" (which notes say is April 5)
    if date_str == "04-05-2026" and "April 5" in notes:
        return datetime.strptime("05-04-2026", "%d-%m-%Y").date(), "Normalized swapped date 04-05-2026 -> 05-04-2026 (April 5th) based on notes context."

    # Try standard dd-mm-yyyy
    for fmt in ["%d-%m-%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt).date(), None
        except ValueError:
            pass
            
    # Try custom formats like "Mar-14"
    match = re.match(r'^([A-Za-z]{3})-(\d{1,2})$', date_str)
    if match:
        month_str, day_str = match.groups()
        # Map month names to numbers
        months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 
                  'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        month_num = months.get(month_str.lower()[:3])
        if month_num:
            # Assume 2026 as that's the year of the dataset
            parsed = date(2026, month_num, int(day_str))
            return parsed, f"Parsed malformed date '{date_str}' as '{parsed.strftime('%d-%m-%Y')}'."
            
    raise ValueError(f"Unable to parse date format: {date_str}")

def normalize_member_name(name):
    """Normalize name casing and map aliases to standard names."""
    name = name.strip()
    if not name:
        return ""
    # Capitalize first letter
    normalized = name.capitalize()
    # Handle known aliases
    aliases = {
        "Priya s": "Priya",
        "Priyas": "Priya",
        "Mera": "Meera",
    }
    return aliases.get(normalized, normalized)

def get_active_members(group_id, expense_date):
    """Fetch active members for a group on a specific date."""
    memberships = GroupMembership.query.filter(
        GroupMembership.group_id == group_id,
        GroupMembership.joined_at <= expense_date
    ).all()
    
    active_users = []
    for m in memberships:
        if m.left_at is None or m.left_at >= expense_date:
            active_users.append(m.user.name)
    return active_users

def run_import(csv_path, group_name="Flat 101"):
    """Parse CSV, detect all anomalies, apply policies, write to database, and return report."""
    report = {
        "total_rows_processed": 0,
        "expenses_imported": 0,
        "settlements_imported": 0,
        "rows_skipped": 0,
        "anomalies": [] # list of dicts: {row_idx, type, details, severity, action}
    }
    
    group = Group.query.filter_by(name=group_name).first()
    if not group:
        raise ValueError(f"Group '{group_name}' not found. Please run seed_db.py first.")
        
    # Read all users to map names to user objects
    all_users = User.query.all()
    user_map = {u.name: u for u in all_users}
    
    seen_signatures = set()
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader, start=2): # Line 1 is headers, data starts at line 2
            report["total_rows_processed"] += 1
            
            raw_date = row.get("date", "")
            raw_description = row.get("description", "")
            raw_paid_by = row.get("paid_by", "")
            raw_amount = row.get("amount", "")
            raw_currency = row.get("currency", "")
            raw_split_type = row.get("split_type", "")
            raw_split_with = row.get("split_with", "")
            raw_split_details = row.get("split_details", "")
            raw_notes = row.get("notes", "")
            
            # 1. Skip Empty Rows
            if not any(row.values()):
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Empty Row", 
                    "details": "Skipped entirely empty row.", "severity": "low", "action": "Skipped"
                })
                continue
                
            # 2. Check for Missing Payer
            if not raw_paid_by.strip():
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Missing Payer", 
                    "details": f"Expense '{raw_description}' skipped due to missing payer.", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue

            # 3. Clean and Parse Date
            try:
                exp_date, date_warning = parse_date_flexible(raw_date, raw_notes)
                if date_warning:
                    report["anomalies"].append({
                        "row": idx, "type": "Malformed Date", "details": date_warning, "severity": "medium", "action": "Normalized"
                    })
            except Exception as e:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Invalid Date Format", 
                    "details": f"Failed to parse date '{raw_date}': {str(e)}", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue
                
            # 4. Normalize Payer Name
            payer_name = normalize_member_name(raw_paid_by)
            if payer_name != raw_paid_by:
                report["anomalies"].append({
                    "row": idx, "type": "Payer Name Casing/Alias Mismatch", 
                    "details": f"Normalized payer '{raw_paid_by}' -> '{payer_name}'.", 
                    "severity": "low", "action": "Normalized"
                })
                
            # Verify payer exists
            if payer_name not in user_map:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Unknown Payer", 
                    "details": f"Payer '{payer_name}' is not a registered user.", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue
            payer_user = user_map[payer_name]
            
            # 5. Clean Amount
            try:
                amount = clean_amount(raw_amount)
                if "," in raw_amount or '"' in raw_amount:
                    report["anomalies"].append({
                        "row": idx, "type": "Amount Format Issue", 
                        "details": f"Cleaned amount formatting '{raw_amount}' -> {amount}.", 
                        "severity": "low", "action": "Parsed to decimal"
                    })
            except Exception as e:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Invalid Amount", 
                    "details": f"Failed to parse amount '{raw_amount}': {str(e)}", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue

            # 6. Check for Zero Amount
            if amount == Decimal('0.00'):
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Zero Amount Expense", 
                    "details": f"Skipped Swiggy/Double-logged record '{raw_description}' as amount is 0.", 
                    "severity": "medium", "action": "Skipped row"
                })
                continue
                
            # 7. Check for Float Precision / Decimal Rounding
            if len(str(amount).split('.')) > 1 and len(str(amount).split('.')[1]) > 2:
                rounded_amount = amount.quantize(Decimal('0.01'))
                report["anomalies"].append({
                    "row": idx, "type": "Float Precision Excess", 
                    "details": f"Rounded amount '{amount}' -> '{rounded_amount}'.", 
                    "severity": "low", "action": "Rounded to 2 decimals"
                })
                amount = rounded_amount

            # 8. Clean Currency
            currency = raw_currency.strip().upper()
            if not currency:
                currency = 'INR'
                report["anomalies"].append({
                    "row": idx, "type": "Missing Currency", 
                    "details": "Currency was empty. Defaulted to INR.", 
                    "severity": "medium", "action": "Defaulted to INR"
                })
            elif currency not in ['INR', 'USD']:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Unsupported Currency", 
                    "details": f"Currency '{currency}' is not supported.", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue

            # Determine conversion rate to INR
            exchange_rate = Decimal('1.0000')
            if currency == 'USD':
                exchange_rate = USD_TO_INR_RATE
                report["anomalies"].append({
                    "row": idx, "type": "USD Transaction Detected", 
                    "details": f"USD Transaction. Calculated conversion at fixed rate of 1 USD = {USD_TO_INR_RATE} INR.", 
                    "severity": "low", "action": "Applied exchange rate conversion"
                })

            # 9. Settlement Check
            # Settlements have empty split_type and split_with is a single user, OR notes indicate it's a settlement.
            is_settlement = False
            split_with_users = [normalize_member_name(u) for u in raw_split_with.split(';') if u.strip()]
            
            if (not raw_split_type.strip() and len(split_with_users) == 1) or "paid" in raw_description.lower() or "deposit" in raw_description.lower():
                is_settlement = True
                
            if is_settlement:
                # Resolve recipient
                recipient_name = split_with_users[0] if split_with_users else None
                if not recipient_name and "paid" in raw_description.lower():
                    # Parse recipient from notes or description (e.g. "Rohan paid Aisha back")
                    for name in user_map.keys():
                        if name != payer_name and name.lower() in raw_description.lower():
                            recipient_name = name
                            break
                            
                if not recipient_name or recipient_name not in user_map:
                    report["rows_skipped"] += 1
                    report["anomalies"].append({
                        "row": idx, "type": "Settlement Parsing Error", 
                        "details": f"Could not determine recipient of settlement: '{raw_description}'.", 
                        "severity": "critical", "action": "Skipped row"
                    })
                    continue
                    
                settlement = Settlement(
                    group_id=group.id,
                    sender_id=payer_user.id,
                    receiver_id=user_map[recipient_name].id,
                    amount=amount,
                    currency=currency,
                    exchange_rate=exchange_rate,
                    date=exp_date
                )
                db.session.add(settlement)
                report["settlements_imported"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Settlement Logged as Expense", 
                    "details": f"Auto-promoted direct transfer '{raw_description}' ({amount} {currency}) to Settlements table.", 
                    "severity": "medium", "action": "Imported as peer-to-peer settlement"
                })
                continue

            # 10. Check for De-duplication (Exact description/payer/amount matches)
            # Create a signature for duplicate detection
            norm_desc_clean = re.sub(r'[^a-zA-Z0-9]', '', raw_description.lower())
            sig = (exp_date, payer_name, norm_desc_clean, amount)
            if sig in seen_signatures:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Duplicate Row Detected", 
                    "details": f"Skipped duplicate expense '{raw_description}' of {amount} {currency} paid by {payer_name}.", 
                    "severity": "medium", "action": "Skipped duplicate row"
                })
                continue
            seen_signatures.add(sig)

            # 11. Parse Split Users and Bounds Check
            # Retrieve active group members on this date
            active_members = get_active_members(group.id, exp_date)
            
            # Map split users, cleaning Kabir or other out-of-scope non-group members
            valid_split_users = []
            for u in split_with_users:
                if u not in user_map:
                    report["anomalies"].append({
                        "row": idx, "type": "Out-of-Scope Split Member", 
                        "details": f"Removed external member '{u}' from split of '{raw_description}'.", 
                        "severity": "high", "action": "Redistributed split among active members"
                    })
                    continue
                
                # Check active bounds
                if u not in active_members:
                    report["anomalies"].append({
                        "row": idx, "type": "Membership Inactive Boundary Violation", 
                        "details": f"Excluded '{u}' from split of '{raw_description}' on {exp_date.strftime('%Y-%m-%d')} because they were not in the group at this date.", 
                        "severity": "high", "action": "Redistributed split among active members"
                    })
                    continue
                valid_split_users.append(u)
                
            if not valid_split_users:
                report["rows_skipped"] += 1
                report["anomalies"].append({
                    "row": idx, "type": "Empty Split List", 
                    "details": f"No active members left to split expense '{raw_description}'.", 
                    "severity": "critical", "action": "Skipped row"
                })
                continue

            # 12. Parse Splits & Allocations
            split_type = raw_split_type.strip().lower()
            if split_type not in ['equal', 'unequal', 'percentage', 'share']:
                split_type = 'equal'
                report["anomalies"].append({
                    "row": idx, "type": "Unknown Split Type", 
                    "details": f"Split type '{raw_split_type}' unknown. Defaulted to equal.", 
                    "severity": "medium", "action": "Defaulted to equal"
                })

            splits_allocation = {}
            for u in valid_split_users:
                splits_allocation[u] = Decimal('0.00')

            # Parse split details (for unequal, percentage, share)
            raw_details_list = [d.strip() for d in raw_split_details.split(';') if d.strip()]
            details_map = {}
            for item in raw_details_list:
                # E.g. "Rohan 700" or "Aisha 30%"
                match = re.match(r'^(.+?)\s+(\d+(\.\d+)?)(%)?$', item)
                if match:
                    name_raw, val_str, _, is_pct = match.groups()
                    name_norm = normalize_member_name(name_raw)
                    if name_norm in valid_split_users:
                        details_map[name_norm] = Decimal(val_str)

            if split_type == 'equal':
                share_val = amount / Decimal(len(valid_split_users))
                for u in valid_split_users:
                    splits_allocation[u] = share_val

            elif split_type == 'unequal':
                # Sum of unequal amounts must equal the total amount
                total_detail_sum = sum(details_map.values())
                if total_detail_sum != amount:
                    report["anomalies"].append({
                        "row": idx, "type": "Unequal Splits Mismatch", 
                        "details": f"Unequal sum ({total_detail_sum}) does not equal total amount ({amount}). Rescaled values.", 
                        "severity": "medium", "action": "Scaled unequal values proportionally"
                    })
                    # Scale them
                    if total_detail_sum > 0:
                        for u in valid_split_users:
                            val = details_map.get(u, Decimal('0.00'))
                            splits_allocation[u] = (val / total_detail_sum) * amount
                    else:
                        share_val = amount / Decimal(len(valid_split_users))
                        for u in valid_split_users:
                            splits_allocation[u] = share_val
                else:
                    for u in valid_split_users:
                        splits_allocation[u] = details_map.get(u, Decimal('0.00'))

            elif split_type == 'percentage':
                # Check if percentages sum to 100%
                pct_sum = sum(details_map.values())
                if pct_sum != Decimal('100.00'):
                    report["anomalies"].append({
                        "row": idx, "type": "Percentage Split Sum Violation", 
                        "details": f"Percentages sum to {pct_sum}% (expected 100%). Rescaled splits to fit 100%.", 
                        "severity": "high", "action": "Scaled percentages to sum to 100%"
                    })
                # Calculate splits scaled to actual sum
                if pct_sum > 0:
                    for u in valid_split_users:
                        pct = details_map.get(u, Decimal('0.00'))
                        splits_allocation[u] = (pct / pct_sum) * amount
                else:
                    share_val = amount / Decimal(len(valid_split_users))
                    for u in valid_split_users:
                        splits_allocation[u] = share_val

            elif split_type == 'share':
                share_sum = sum(details_map.values())
                if share_sum > 0:
                    for u in valid_split_users:
                        sh = details_map.get(u, Decimal('0.00'))
                        splits_allocation[u] = (sh / share_sum) * amount
                else:
                    share_val = amount / Decimal(len(valid_split_users))
                    for u in valid_split_users:
                        splits_allocation[u] = share_val

            # Write Expense to DB
            expense = Expense(
                group_id=group.id,
                payer_id=payer_user.id,
                description=raw_description,
                amount=amount,
                currency=currency,
                exchange_rate=exchange_rate,
                date=exp_date
            )
            db.session.add(expense)
            db.session.flush() # Generate ID for splits

            # Write Expense Splits to DB
            for user_name, owed in splits_allocation.items():
                split_ratio = None
                if split_type == 'percentage':
                    split_ratio = details_map.get(user_name, Decimal('0.00'))
                elif split_type == 'share':
                    split_ratio = details_map.get(user_name, Decimal('0.00'))
                    
                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=user_map[user_name].id,
                    amount_owed=owed.quantize(Decimal('0.01')),
                    split_ratio=split_ratio
                )
                db.session.add(split)

            report["expenses_imported"] += 1
            
        db.session.commit()
        
    return report
