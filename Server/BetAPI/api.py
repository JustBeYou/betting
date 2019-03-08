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

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/matches')
def matches():
    return jsonify(matches=[i.json for i in Match.query.all()])

@api.route('/odds/<id>')
def odds(id):
    return None
