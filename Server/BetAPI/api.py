"""A custom API blueprint.

This api module is *additional* to the CRUD API exposed by Flask-Restless. It
should be used only when a custom, non-CRUD, API is necessary.

"""

from flask import Blueprint, request, redirect, jsonify
from json import loads
from pprint import pprint
from time import time, sleep
from datetime import datetime, timedelta
from threading import Thread
from BetAPI.model import db, Match
from BetAPI.cache import Cache
from BetAPI.oddfeedsApi import getOddsForMatch, BOOKMAKERS, ODD_TYPES
from BetAPI.config import TARGET_BOOKMAKERS, TARGET_ODDS

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/matches')
def matches():
    return jsonify(matches=[i.json for i in Match.query.all()])

@api.route('/matches/<id>')
def odds(id):
    cache = Cache.get_store()
    if id not in cache.keys():
        data = getOddsForMatch(
          id,
          TARGET_BOOKMAKERS,
          TARGET_ODDS
        )

        to_add = []
        for odd in data["odds"]["prematch"]:
            to_add.append(odd)
        for odd in data["odds"]["inplay"]:
            to_add.append(odd)
        cache[id] = to_add


    return jsonify(odds=[i for i in cache[id]])
