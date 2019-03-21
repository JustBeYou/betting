import logging

from flask import Flask, request, render_template, jsonify, redirect
from flask_bootstrap import Bootstrap
from flask_cors import CORS
from flask_restless import APIManager, ProcessingException
from flask_security import (
  RoleMixin,
  SQLAlchemyUserDatastore,
  Security,
  UserMixin,
  auth_token_required,
  current_user,
  login_required,
)
from werkzeug.security import gen_salt

from BetManager.api import api
from BetManager.middleware import LoggingMiddleware
from BetManager.model import make_conn_str, db, Match, History
from BetManager.mainApi import *
import BetManager.bot as bot

from sqlalchemy import desc, asc
from multiprocessing import Process
from time import sleep
from datetime import datetime
from base64 import b64encode, b64decode
from json import loads, dumps

import logging
import logging.config
import yaml
logging.config.dictConfig(yaml.load(open(LOGGING_CONFIG, 'r'), Loader=yaml.FullLoader))

app = Flask(__name__)

def restless_api_auth_func(*args, **kw):
    @auth_token_required
    def check_authentication():
        return
    rsp = check_authentication()
    if rsp and rsp.status_code in [401]:
        raise ProcessingException(description='Not authenticated!', code=401)

def matches_updater(db):
    session = db.create_scoped_session()
    while True:
        feed = getMatches()['matches']
        ids = [x['id'] for x in feed]

        matches = session.query(Match).with_for_update().all()
        already = []
        for match in matches:
            if match.id not in ids:
                session.delete(match)
            else:
                already.append(match.id)
        session.commit()

        for match in feed:
            if match['id'] not in already:
                time = datetime.strptime(match['time'], "%a, %d %b %Y %H:%M:%S %Z")
                m = Match(match['id'], time, match['home'], match['away'], match['live'])
                session.add(m)
            else:
                m = session.query(Match).filter(Match.id == match['id']).with_for_update().first()
                if match['live'] != m.live:
                    m.live = match['live']
                session.commit()

        session.commit()

        sleep(60 * MATCHES_UPDATE_INTERVAL)

def init_webapp():
    def to_bytes(s):
        return bytes(s, encoding="utf8")

    app.add_template_filter(to_bytes)
    app.add_template_filter(dumps)
    app.add_template_filter(b64encode)
    app.add_template_filter(b64decode)
    app.register_blueprint(api, url_prefix='/api')

    app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'S0m37h1ng_S0m37h1ng_S3kr1t_K3y____!@#$'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = 'S0m37h1ng_S0m37h1ng_S3kr1t_CSRF_K3y____!@#$'
    app.config['SECURITY_TOKEN_MAX_AGE'] = 60
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Auth-Token'

    CORS(app, supports_credentials=True)
    Bootstrap(app)

    db.app = app
    db.init_app(app)
    db.create_all()

    p = Process(target=matches_updater, args=(db,))
    p.daemon = True
    p.start()

    return app

@app.route('/')
def index():
    return render_template('index.html', matches=Match.query.order_by(asc(Match.time)).all())

def str_float(x):
    return "{:.2f}".format(x)

@app.route('/surebets')
def surebets():
    return render_template('surebets.html')

@app.route('/history')
def history():
    return render_template('history.html', history = History.query.order_by(desc(History.time)).all())
