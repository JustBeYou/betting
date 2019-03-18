from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy import Column, Integer, String
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required

db = SQLAlchemy()

class Match(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    time = db.Column(db.DateTime())
    home = db.Column(db.String(255))
    away = db.Column(db.String(255))
    live = db.Column(db.Boolean())
    def __init__(self, id, time, home, away, live):
        self.id = id
        self.time = time
        self.home = home
        self.away = away
        self.live = live

    @property
    def json(self):
        return {
                "id":self.id,
                "time":self.time,
                "home":self.home,
                "away":self.away,
                "live":self.live
        }

def make_conn_str():
    return 'sqlite:///BetAPI.db'
