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
from sqlalchemy import desc, asc

from multiprocessing import Process
from time import sleep
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Initialize Flask and register a blueprint
app = Flask(__name__)

def restless_api_auth_func(*args, **kw):
    """A request processor that ensures requests are authenticated.

    Flask-Restless endpoints are generated automatically and thus do not have a
    Flask route function that we can decorate with the
    :func:`flask_security.auth_token_required` decorator. This function
    mimics the route function and satisfies the Flask-Restless request processor
    contract.

    """
    @auth_token_required
    def check_authentication():
        return
    rsp = check_authentication()
    # TODO(sholsapp): There are additional response codes that would result in
    # processing exceptions, this need to be addressed here.
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

from base64 import b64encode, b64decode
from json import dumps

def init_webapp():
    """Initialize the web application."""

    # logging.getLogger('flask_cors').level = logging.DEBUG
    # app.wsgi_app = LoggingMiddleware(app.wsgi_app)

    # Note, this url namespace also exists for the Flask-Restless
    # extension and is where CRUD interfaces live, so be careful not to
    # collide with model names here. We could change this, but it's nice
    # to have API live in the same url namespace.
    def to_bytes(s):
        return bytes(s, encoding="utf8")

    app.add_template_filter(to_bytes)
    app.add_template_filter(dumps)
    app.add_template_filter(b64encode)
    app.add_template_filter(b64decode)
    app.register_blueprint(api, url_prefix='/api')

    # Initialize Flask configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
    app.config['SECRET_KEY'] = 'S0m37h1ng_S0m37h1ng_S3kr1t_K3y____!@#$'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = 'S0m37h1ng_S0m37h1ng_S3kr1t_CSRF_K3y____!@#$'
    app.config['SECURITY_TOKEN_MAX_AGE'] = 60
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Auth-Token'
    # app.config['SECURITY_POST_LOGIN_VIEW'] = 'http://127.0.0.1:4200'
    # app.config['CORS_HEADERS'] = 'Content-Type'

    # Initialize Flask-CORS
    CORS(app, supports_credentials=True)
    # CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

    # Initialize Flask-Bootstrap
    Bootstrap(app)

    # Initialize Flask-Security
    #user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    #security = Security(app, user_datastore)

    # Initialize Flask-SQLAlchemy
    db.app = app
    db.init_app(app)
    db.create_all()

    p = Process(target=matches_updater, args=(db,))
    p.daemon = True
    p.start()

    # Initialize Flask-Restless
    #manager = APIManager(
    #  app,
    #  flask_sqlalchemy_db=db,
    #  preprocessors=dict(GET_MANY=[restless_api_auth_func]),
    #)
    #manager.create_api(Employee, methods=['GET', 'POST', 'OPTIONS'])
    return app

@app.route('/')
def index():
    return render_template('index.html', matches=Match.query.order_by(asc(Match.time)).all())

from base64 import b64decode
from json import loads
import BetManager.bot as bot

def str_float(x):
    return "{:.2f}".format(x)

@app.route('/surebets', methods=['GET', 'POST'])
def surebets():
    if request.method == 'GET':
        feed = getSureBets()["surebets"]
        feed = [feed[i:i+2] for i in range(0, len(feed), 2)]

        return render_template('surebets.html', bets_rows = feed, mapping = ODD_TYPES_IDS)

    elif request.method == 'POST':
        try:
            data = loads(b64decode(request.form['bet'].replace('b\'', '').replace('\'', '')))
            max_amount = int(request.form['max_amount'])
            to_add = []
            for k in data.keys():
                if k == "-1" or k == "-2": continue
                to_bet = float(str_float(max_amount / data[k]["price"]))
                h = History(data["-1"]['id'], data["-1"]["home"], data["-1"]["away"], ODD_TYPES_IDS[data[k]["type_id"]], data[k]["price"], to_bet)
                to_add.append(h)
                nav = loads(data[k]["nav"])
                nav["type_id"] = data[k]["type_id"]
                nav["hc"] = data[k]["hc"]

                print (data[k]["bookmaker"]["name"])
                print (data[k])
                bot.login(data[k]["bookmaker"]["name"])
                bot.bet(data[k]["bookmaker"]["name"], nav, to_bet)

            for e in to_add:
                db.session.add(e)
            db.session.commit()
        except Exception as e:
            return "Can't bet: {}".format(e)

        return redirect('/surebets', code=302)

@app.route('/history')
def history():
    return render_template('history.html', history = History.query.order_by(asc(History.time)).all())
