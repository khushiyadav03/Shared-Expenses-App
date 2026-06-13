from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    memberships = db.relationship('GroupMembership', backref='user', lazy=True)
    paid_expenses = db.relationship('Expense', backref='payer', lazy=True)
    sent_settlements = db.relationship('Settlement', foreign_keys='Settlement.sender_id', backref='sender', lazy=True)
    received_settlements = db.relationship('Settlement', foreign_keys='Settlement.receiver_id', backref='receiver', lazy=True)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    memberships = db.relationship('GroupMembership', backref='group', lazy=True)
    expenses = db.relationship('Expense', backref='group', lazy=True)
    settlements = db.relationship('Settlement', backref='group', lazy=True)

class GroupMembership(db.Model):
    __tablename__ = 'group_memberships'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    joined_at = db.Column(db.Date, nullable=False)
    left_at = db.Column(db.Date, nullable=True) # NULL if currently active

    __table_args__ = (db.UniqueConstraint('group_id', 'user_id', name='unique_membership'),)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR') # 'USD' or 'INR'
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=False, default=1.0000) # Rate to convert to INR
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    splits = db.relationship('ExpenseSplit', backref='expense', lazy=True, cascade='all, delete-orphan')

class ExpenseSplit(db.Model):
    __tablename__ = 'expense_splits'
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount_owed = db.Column(db.Numeric(12, 2), nullable=False)
    split_ratio = db.Column(db.Numeric(10, 4), nullable=True) # percentage or share coefficient

    __table_args__ = (db.UniqueConstraint('expense_id', 'user_id', name='unique_expense_user_split'),)

class Settlement(db.Model):
    __tablename__ = 'settlements'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='INR')
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=False, default=1.0000)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
