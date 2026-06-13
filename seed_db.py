import os
from flask import Flask
from models import db, User, Group, GroupMembership
from datetime import datetime
from werkzeug.security import generate_password_hash

def seed():
    app = Flask(__name__)
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///shared_expenses.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Drop and create tables to start fresh
        db.drop_all()
        db.create_all()
        
        print("Database tables created.")
        
        # Create users
        users_data = [
            {"name": "Aisha", "email": "aisha@flat.com", "password": "aisha123"},
            {"name": "Rohan", "email": "rohan@flat.com", "password": "rohan123"},
            {"name": "Priya", "email": "priya@flat.com", "password": "priya123"},
            {"name": "Meera", "email": "meera@flat.com", "password": "meera123"},
            {"name": "Sam", "email": "sam@flat.com", "password": "sam123"},
            {"name": "Dev", "email": "dev@flat.com", "password": "dev123"}
        ]
        
        user_objects = {}
        for u in users_data:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"])
            )
            db.session.add(user)
            user_objects[u["name"]] = user
            
        db.session.flush() # Populate IDs
        print(f"Seeded {len(users_data)} users.")
        
        # Create default group
        group = Group(name="Flat 101")
        db.session.add(group)
        db.session.flush()
        print(f"Created group: {group.name}")
        
        # Create memberships
        memberships = [
            GroupMembership(group_id=group.id, user_id=user_objects["Aisha"].id, joined_at=datetime.strptime("01-02-2026", "%d-%m-%Y").date(), left_at=None),
            GroupMembership(group_id=group.id, user_id=user_objects["Rohan"].id, joined_at=datetime.strptime("01-02-2026", "%d-%m-%Y").date(), left_at=None),
            GroupMembership(group_id=group.id, user_id=user_objects["Priya"].id, joined_at=datetime.strptime("01-02-2026", "%d-%m-%Y").date(), left_at=None),
            GroupMembership(group_id=group.id, user_id=user_objects["Meera"].id, joined_at=datetime.strptime("01-02-2026", "%d-%m-%Y").date(), left_at=datetime.strptime("31-03-2026", "%d-%m-%Y").date()),
            GroupMembership(group_id=group.id, user_id=user_objects["Sam"].id, joined_at=datetime.strptime("15-04-2026", "%d-%m-%Y").date(), left_at=None),
            GroupMembership(group_id=group.id, user_id=user_objects["Dev"].id, joined_at=datetime.strptime("01-02-2026", "%d-%m-%Y").date(), left_at=datetime.strptime("31-03-2026", "%d-%m-%Y").date())
        ]
        
        for m in memberships:
            db.session.add(m)
            
        db.session.commit()
        print("Database successfully seeded.")
        
        # Auto-import default dataset if present
        csv_path = "Expenses Export.csv"
        if os.path.exists(csv_path):
            print(f"Auto-importing dataset: {csv_path}")
            from importer import run_import
            report = run_import(csv_path)
            print(f"Successfully auto-imported {report['expenses_imported']} expenses and {report['settlements_imported']} settlements.")
        else:
            print("Expenses Export.csv not found, skipping auto-import.")

if __name__ == "__main__":
    seed()
