"""A custom API blueprint.

This api module is *additional* to the CRUD API exposed by Flask-Restless. It
should be used only when a custom, non-CRUD, API is necessary.

"""

from flask import Blueprint, request, redirect
from oddfeedsApi import *
from model import db, Match, Odd, Bookmaker, Job, Cluster, History
import bot
from json import loads
from pprint import pprint
from time import time, sleep
from datetime import datetime, timedelta
from threading import Thread

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

import random

def random_outcome():
    foo = [False, True]
    secure_random = random.SystemRandom()
    return secure_random.choice(foo)
last_time = datetime.now()

def background_job():
    global last_time
    sleep(5)
    while True:
        jobs = Job.query.all()
        for job in jobs:
            for cluster in job.clusters:
                if len(cluster.odds):
                    first = cluster.odds[0]
                    if first.amount == 0:
                        first.amount = cluster.initial_bet + cluster.loss * first.price
                        try:
                            pass
                            #print (bet_helper(first.id, first.amount))
                        except:
                            db.session.delete(first)
                    elif datetime.now()-last_time > timedelta(seconds=3):
                        win = random_outcome()
                        last_time = datetime.now()

                        if win:
                            first.loss = 0
                            h = History(first.match.home, first.match.away, first.match.time,
                                        first.type_id, first.price, first.amount, "Win", first.price * first.amount)
                            db.session.add(h)
                            db.session.delete(first)
                        else:
                            cluster.loss += first.amount
                            h = History(first.match.home, first.match.away, first.match.time,
                                        first.type_id, first.price, first.amount, "Lost", -first.amount)
                            db.session.add(h)
                            db.session.delete(first)

                    # match ends
                    #elif (first.match.time + timedelta(minutes=95)) > datetime.now():
                        # get outcome
                        pass

                if (len(cluster.odds) == 0):
                    db.session.delete(cluster)

            db.session.commit()
            if len(job.clusters) == 0:
                db.session.delete(job)

        db.session.commit()
        print ("Baaaaaaaaaaaaaaaaaaaaaackground")
        sleep(10)

th = Thread(target=background_job)
th.daemon = True
th.start()

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
        cluster = Cluster(job.id, 1)
        db.session.add(cluster)
        db.session.commit()

        for m_id in data:
            try:
                print (m_id)
                odds = Odd.query.filter((Odd.match_id == m_id) & ((Odd.type_id == ODD_TYPES["1"]) | (Odd.type_id == ODD_TYPES["2"])) & (Odd.period_id == 1)).all()

                # betting on favourite
                if odds[0].price < odds[1].price:
                    print ("FAVOURITE BET IS: {}".format(odds[0].type_id))
                    odds[0].cluster_id = cluster.id
                else:
                    odds[1].cluster_id = cluster.id
                    print ("FAVOURITE BET IS: {}".format(odds[1].type_id))
            except:
                pass
    db.session.commit()

    return redirect('/jobs', code=302)
