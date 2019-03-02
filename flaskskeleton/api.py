"""A custom API blueprint.

This api module is *additional* to the CRUD API exposed by Flask-Restless. It
should be used only when a custom, non-CRUD, API is necessary.

"""

from flask import Blueprint, request
from oddfeedsApi import *
from model import db, Match, Odd, Bookmaker
import bot
from json import loads
from pprint import pprint

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/')
def status():
    return 'GOOD'

@api.route('/bet', methods=['POST'])
def bet():
    odd_id = request.form['oddId']
    amount = request.form['amount']

    odd_obj = Odd.query.filter_by(id=odd_id).first()
    bookmaker = odd_obj.bookmaker.name
    nav = loads(odd_obj.nav)
    pprint (nav)

    bot.login(bookmaker)
    if not bot.bet(bookmaker, nav, amount):
        return "insufficient funds"

    return "Betting on {} with {}$".format(odd_id, amount)

@api.route('/init')
def init():
    b = Bookmaker(10, "Pinnacle")
    db.session.add(b)
    b = Bookmaker(55, "1xBet")
    db.session.add(b)
    db.session.commit()


    return 'OK'

from time import time

@api.route('/update')
def update():
    start_t = time()

    bks = [
    BOOKMAKERS["Pinnacle"],
    BOOKMAKERS["1xBet"]
    ]
    tps = [
        ODD_TYPES["1"],
        ODD_TYPES["X"],
        ODD_TYPES["2"]
    ]
    data = getData(bks, tps)

    for match in data['matches']:
        exists = Match.query.filter_by(id=int(match['id'])).first()
        if not exists:
            m = Match(int(match['id']), match['start'], match['teams']['home'], match['teams']['away'])
            db.session.add(m)

    for odd in data['odds']["prematch"]:
        exists = Odd.query.filter_by(id=int(odd['id'])).first()
        if not exists:
            o = Odd(odd['id'], odd['match_id'], odd['bookmaker']['id'], odd['type_id'], odd['price'], "prematch", odd['period_id'], odd['nav'])
            db.session.add(o)

    for odd in data['odds']["inplay"]:
        exists = Odd.query.filter_by(id=int(odd['id'])).first()
        if not exists:
            o = Odd(odd['id'], odd['match_id'], odd['bookmaker']['id'], odd['type_id'], odd['price'], "inplay", odd['period_id'], odd['nav'])
            db.session.add(o)

    print ("Update took {}s".format(time() - start_t))
    db.session.commit()

    return 'OK'
