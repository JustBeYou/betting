import logging

from flask import Flask, request, render_template, jsonify
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

from BetAPI.api import api
from BetAPI.middleware import LoggingMiddleware
from BetAPI.model import make_conn_str, db, Match
from sqlalchemy import desc, asc
from threading import Thread
from multiprocessing import Process
from time import sleep
from BetAPI.oddfeedsApi import *
from BetAPI.BetFinder import surebet_thread
from datetime import datetime, timedelta
from BetAPI.cache import Cache
from BetAPI.config import *

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

def updater_thread(db):
    session = db.create_scoped_session()
    while True:
        print ("[*] Starting update...")
        data = getData(
                TARGET_BOOKMAKERS,
                []
                )
        for match in data['matches']:
            exists = session.query(Match).filter_by(id=match['id']).first()
            if not exists:
                try:
                    start = datetime.strptime(match['start'], "%Y-%m-%dT%H:%M:%S")
                except:
                    start = datetime.strptime(match['start'], "%Y-%m-%d")

                m = Match(match['id'], start, match['teams']['home'], match['teams']['away'], match['active']['inplay'])
                session.add(m)
            else:
                m = session.query(Match).with_for_update().filter_by(id=match['id']).first()

                if not match['active']['inplay'] and not match['active']['prematch']:
                    session.delete(m)
                else:
                    m.live = match['active']['inplay']

            session.commit()

        now = datetime.utcnow() - timedelta(minutes=MATCH_LIFETIME)
        outdated = session.query(Match).with_for_update().filter(Match.time < now).all()
        for m in outdated:
            session.delete(m)
        session.commit()

        print ("[*] Update done...")
        sleep(60 * MATCH_LIST_UPDATE_INTERVAL)

def init_webapp():
    """Initialize the web application."""

    # logging.getLogger('flask_cors').level = logging.DEBUG
    # app.wsgi_app = LoggingMiddleware(app.wsgi_app)

    # Note, this url namespace also exists for the Flask-Restless
    # extension and is where CRUD interfaces live, so be careful not to
    # collide with model names here. We could change this, but it's nice
    # to have API live in the same url namespace.
    app.register_blueprint(api, url_prefix='/api')

    # Initialize Flask configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #app.config['SQLALCHEMY_POOL_SIZE'] = 5
    #app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600

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

    # Initialize Flask-Restless
    #manager = APIManager(
    #  app,
    #  flask_sqlalchemy_db=db,
    #  preprocessors=dict(GET_MANY=[restless_api_auth_func]),
    #)
    #manager.create_api(Employee, methods=['GET', 'POST', 'OPTIONS'])

    # Init other workers
    #t = Thread(target=updater_thread, args=(db,))
    t1 = Process(target=updater_thread, args=(db,))
    t1.daemon = True
    t1.start()

    t2 = Process(target=surebet_thread, args=(db, Cache.get_store()))
    t2.daemon = True
    t2.start()

    return app

