from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy import Column, Integer, String
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
from datetime import datetime

db = SQLAlchemy()

class Match(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.DateTime())
    home = db.Column(db.String(255))
    away = db.Column(db.String(255))
    live = db.Column(db.Boolean)
    def __init__(self, id, time, home, away, live):
        self.id = id
        self.time = time
        self.home = home
        self.away = away
        self.live = live

class History(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    # match info
    match_id = db.Column(db.Integer())
    home = db.Column(db.String(255))
    away = db.Column(db.String(255))

    # odd info
    odd_type = db.Column(db.String(255))
    price = db.Column(db.Float())

    # bet info
    time = db.Column(db.DateTime())
    amount = db.Column(db.Float())

    def __init__(self, match_id, home, away, odd_type, price, amount):
        self.match_id = match_id
        self.home = home
        self.away = away
        self.odd_type = odd_type
        self.price = price
        self.time = datetime.now()
        self.amount = amount

def make_conn_str():
    """Make an local database file on disk."""
    return 'sqlite:///BetManager.db'
