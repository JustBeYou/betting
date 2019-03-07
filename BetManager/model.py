from flask.ext.sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy import Column, Integer, String
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required


db = SQLAlchemy()

class Match(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.DateTime())
    home = db.Column(db.String(255))
    away = db.Column(db.String(255))
    odds = db.relationship('Odd', backref='match', lazy=True)
    def __init__(self, id, time, home, away):
        self.id = id
        self.time = time
        self.home = home
        self.away = away

class Bookmaker(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    odds = db.relationship('Odd', backref='bookmaker', lazy=True)
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Odd(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    when = db.Column(db.String(255))
    type_id = db.Column(db.Integer())
    price = db.Column(db.Float())
    period_id = db.Column(db.Integer())
    match_id = db.Column(db.Integer(), db.ForeignKey('match.id'), nullable=False)
    bookmaker_id = db.Column(db.Integer(), db.ForeignKey('bookmaker.id'), nullable=False)
    nav = db.Column(db.String(2048))

    # only used when it is used by a job
    cluster_id = db.Column(db.Integer(), db.ForeignKey('cluster.id'), nullable=True)
    amount = db.Column(db.Float())
    def __init__(self, id, match_id, bookmaker_id, type_id, price, when, period_id, nav):
        self.id = id
        self.match_id = match_id
        self.bookmaker_id = bookmaker_id
        self.type_id = type_id
        self.price = price
        self.when = when
        self.period_id = period_id
        self.nav = nav
        self.amount = 0.0

class Cluster(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    odds = db.relationship('Odd', backref='cluster', lazy=True)
    job_id = db.Column(db.Integer(), db.ForeignKey('job.id'), nullable=False)
    loss = db.Column(db.Float())
    initial_bet = db.Column(db.Float())

    def __init__(self, job_id, initial_bet):
        self.job_id = job_id
        self.initial_bet = initial_bet
        self.loss = 0

class Job(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    clusters = db.relationship('Cluster', backref='job', lazy=True)

    def __init__(self):
        pass

class History(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    home = db.Column(db.String(255))
    away = db.Column(db.String(255))
    time = db.Column(db.DateTime())
    type_id = db.Column(db.Integer())
    price = db.Column(db.Float())
    amount = db.Column(db.Float())
    outcome = db.Column(db.String(255))
    profit = db.Column(db.Float())

    def __init__(self, home, away, time, type_id, price, amount, outcome, profit):
        self.home = home
        self.away = away
        self.time = time
        self.type_id = type_id
        self.price = price
        self.amount = amount
        self.outcome = outcome
        self.profit = profit

def make_conn_str():
    """Make an local database file on disk."""
    return 'sqlite:///BetManager.db'
