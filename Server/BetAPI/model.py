from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from sqlalchemy import Column, Integer, String
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required


db = SQLAlchemy()

def make_conn_str():
    """Make an local database file on disk."""
    return 'sqlite:///BetAPI.db'
