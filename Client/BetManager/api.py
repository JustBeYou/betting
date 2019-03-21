from flask import Blueprint, request, redirect, jsonify
from BetManager.model import db, Match, History
from BetManager.mainApi import *
import BetManager.bot as bot
from json import loads
from pprint import pprint
from time import time, sleep
from datetime import datetime, timedelta
from threading import Thread
import sqlite3
import logging

api = Blueprint('api', __name__, template_folder='templates')

def str_float(x):
    return "{:.2f}".format(x)

@api.route('/surebets', methods=['GET'])
def get_surebets():
    return jsonify(getSureBets())

bet_in_progress = False

@api.route('/surebets', methods=['POST'])
def do_surebets():
    global bet_in_progress
    if bet_in_progress:
        return jsonify({"message":"Bet in progress."})

    bet_in_progress = True
    req_data = request.get_json()
    try:
        data = req_data["bet"]
        max_amount = int(req_data["max_amount"])
        to_add = []
        for k in data["odds"].keys():
            to_bet = float(str_float(max_amount / data["odds"][k]["price"]))
            h = History(data["match"]['id'],
                        data["match"]["home"],
                        data["match"]["away"],
                        ODD_TYPES_IDS[data["odds"][k]["type_id"]],
                        data["odds"][k]["price"], to_bet)
            to_add.append(h)
            nav = loads(data["odds"][k]["nav"])
            nav["type_id"] = data["odds"][k]["type_id"]
            nav["hc"] = data["odds"][k]["hc"]

            logging.info(data)
            bot.login(data["odds"][k]["bookmaker"]["name"])
            bot.bet(data["odds"][k]["bookmaker"]["name"], nav, to_bet)

        for e in to_add:
            db.session.add(e)
        db.session.commit()
    except Exception as e:
        bet_in_progress = False
        logging.warn("Can't bet: {}".format(e))
        return jsonify({"message": str(e)})

    bet_in_progress = False
    return jsonify({"message": "ok"})
