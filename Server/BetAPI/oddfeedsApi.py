from requests import session
from pprint import pprint
from multiprocessing import Pool
from time import sleep

s = session()
url = "http://www.oddstorm.com/feeds_api/"

ODD_TYPES = {
    "1": 2,
    "X": 3,
    "2": 4,
    "1X": 5,
    "12": 6,
    "X2": 7,
    "Over": 8,
    "Under": 9
}

BOOKMAKERS = {
    "Bet365": 26,
    "Pinnacle": 10,
    "1xBet": 55,
    "BetfairExchange": 47
}
UPDATE_PREMATCH = True
UPDATE_LIVE     = True

def getTournaments():
    try:
        resp = s.post(url, json={
                "prematch": UPDATE_PREMATCH,
                "inplay": UPDATE_LIVE
            })
        return resp.json()
    except:
        return {}

def getLeagues(tournaments):
    data = tournaments['data']
    ids = []
    for e in data:
        ids.append(e['id'])

    ids = [ids[i:i+100] for i in range(0, len(ids), 100)]

    leagues = []
    for e in ids:
        try:
            resp = s.post(url, json={
                "scope": "leagues",
                "tournament_ids":e,
                "prematch":UPDATE_PREMATCH,
                "inplay":UPDATE_LIVE
                })
            leagues.append(resp.json())
        except:
            pass

    return leagues

def getMatches(leagues):
    ids = []
    for l in leagues:
        for e in l['data']:
            ids.append(e['id'])

    ids = [ids[i:i+100] for i in range(0, len(ids), 100)]

    matches = []
    for e in ids:
        try:
            resp = s.post(url, json={
                "scope":"matches",
                "league_ids":e,
                "prematch":UPDATE_PREMATCH,
                "inplay":UPDATE_LIVE
                })
            matches.append(resp.json())
        except:
            pass

    return matches

def worker_getOdds(config):
    ids = config['ids']
    bookmakers = config['bookmakers']
    types = config['types']
    worker = config['worker']

    ids = [ids[i:i+25] for i in range(0, len(ids), 25)]

    odds = []
    i = 1
    for e in ids:
        i += 1
        try:
            resp = s.post(url, json={
                "scope":"odds",
                "match_ids":e,
                "bookmaker_ids":bookmakers,
                "odd_type_ids":types,
                "odd_period_ids":[1, 0, 6],
                "prematch":UPDATE_PREMATCH,
                "inplay":UPDATE_LIVE
                })

            r = resp.json()
            odds.append(r)
        except Exception as e:
            logging.warn("[ERROR] {}".format(e))
    return odds

def getOdds(cnt, ids, bookmakers, types):
    config = {
        "worker": cnt,
        "ids": ids,
        "bookmakers":bookmakers,
        "types":types
    }

    r = worker_getOdds(config)

    odds = {
        "prematch": [],
        "inplay": []
    }
    for ll in r:
        odds["prematch"] += ll['data']['prematch']
        odds["inplay"]   += ll['data']['inplay']

    return odds


def getData(bookmakers, types, get_odds=False):
    tournaments = getTournaments()
    leagues = getLeagues(tournaments)
    matches = getMatches(leagues)

    __matches = []
    ids = []
    for m in matches:
        for e in m['data']:
            __matches.append(e)
            ids.append(e['id'])

    if get_odds:
        return {'matches':__matches, 'odds':getOdds(1, ids, bookmakers, types)}
    return {'matches':__matches, 'odds':{'prematch':[],'inplay':[]}}


def getOddsForMatch(id, bookmakers, types):
    return {'odds':getOdds(1, [id], bookmakers, types)}

def getOddsForMatches(ids,bookmakers,types):
    return {'odds':getOdds(1, ids, bookmakers, types)}
