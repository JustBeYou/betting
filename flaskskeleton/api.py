"""A custom API blueprint.

This api module is *additional* to the CRUD API exposed by Flask-Restless. It
should be used only when a custom, non-CRUD, API is necessary.

"""

from flask import Blueprint, request, redirect
from oddfeedsApi import *
from model import db, Match, Odd, Bookmaker, Job, Cluster
import bot
from json import loads
from pprint import pprint

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/')
def status():
    return 'GOOD'

def bet_helper(odd_id, amount):
    odd_obj = Odd.query.filter_by(id=odd_id).first()
    bookmaker = odd_obj.bookmaker.name
    nav = loads(odd_obj.nav)
    pprint (nav)

    bot.login(bookmaker)
    if not bot.bet(bookmaker, nav, amount):
        return "insufficient funds"

    return "Betting on {} with {}$".format(odd_id, amount)
@api.route('/bet', methods=['POST'])
def bet():
    odd_id = request.form['oddId']
    amount = request.form['amount']
    return bet_helper(odd_it, amount)

@api.route('/init')
def init():
    b = Bookmaker(10, "Pinnacle")
    db.session.add(b)
    b = Bookmaker(55, "1xBet")
    db.session.add(b)
    db.session.commit()


    return redirect('/api/update', code=302)

from time import time
from datetime import datetime

@api.route('/update')
def update():
    start_t = time()

    bks = [
    BOOKMAKERS["Pinnacle"]
    #BOOKMAKERS["1xBet"]
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
            try:
                start = datetime.strptime(match['start'], "%Y-%m-%dT%H:%M:%S")
            except:
                start = datetime.strptime(match['start'], "%Y-%m-%d")

            m = Match(int(match['id']), start, match['teams']['home'], match['teams']['away'])
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

    return redirect('/', code=302)

import collections

@api.route('/strategy1', methods=['POST'])
def strategy1():
    bookmaker  = request.form.get('bookmaker')
    matchesIds = request.form.getlist('matchesIds')
    d = {}
    max_cluster = 0
    for e in matchesIds:
        id = int(e)
        start = Match.query.filter_by(id=id).first().time
        try:
            d[start].append(id)
        except:
            d[start] = [id]
        max_cluster = max(max_cluster, len(d[start]))

    d = collections.OrderedDict(sorted(d.items()))

    clusters = [[] for i in range(max_cluster)]
    for k, v in d.iteritems():
        print (v)
        for i, w in enumerate(v):
            print (i, w)
            clusters[i].append(w)

    print (clusters)

    job = Job()
    db.session.add(job)
    db.session.commit()

    for data in clusters:
        cluster = Cluster(job.id)
        db.session.add(cluster)
        db.session.commit()

        for m_id in data:
            print (m_id)
            odds = Odd.query.filter((Odd.match_id == m_id) & ((Odd.type_id == ODD_TYPES["1"]) | (Odd.type_id == ODD_TYPES["2"])) & (Odd.period_id == 1)).all()

            # betting on favourite
            if odds[0].price < odds[1].price:
                print ("FAVOURITE BET IS: {}".format(odds[0].type_id))
                odds[0].cluster_id = cluster.id
            else:
                odds[1].cluster_id = cluster.id
                print ("FAVOURITE BET IS: {}".format(odds[1].type_id))
    db.session.commit()

    return redirect('/jobs', code=302)
