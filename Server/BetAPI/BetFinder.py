# module for finding the best sure bet for a match.
# author: Gabi Tulba
class BetFinder:
    def __init__(self, match, sureBets):
        self.match = match
        self.sureBets = sureBets
        self.bestBets = {}
        self.periods = {}
        self.bestBet = {}
        self.bestPrice = 1.0
        self.__findBestBet()

    def __findBestBet(self):
        try:
            for odd in self.match["odds"]:
                if odd["hc"] != 0: continue
                if not odd["period_id"] in self.periods:
                    self.periods[odd["period_id"]] = 1
                    self.bestBets[odd["period_id"]] = {odd["type_id"]:odd}
                elif not odd["type_id"] in self.bestBets[odd["period_id"]]:
                    self.bestBets[odd["period_id"]][odd["type_id"]] = odd
                elif odd["price"] > self.bestBets[odd["period_id"]][odd["type_id"]]["price"]:
                    self.bestBets[odd["period_id"]][odd["type_id"]] = odd

            for period_id in self.periods:
                current = {}
                priceSum = 0
                try:
                    for sureBet in self.sureBets:
                        for type_id in sureBet:
                            current[type_id] = self.bestBets[period_id][type_id]
                except:
                    continue

                for type_id in current:
                    odd = current[type_id]
                    priceSum += 1.0 / odd["price"]

                if(priceSum < self.bestPrice):
                    self.bestPrice = priceSum
                    self.bestBet = current
        except:
            return "Match format error!"

    def printBestBet(self):
        if(len(self.bestBet) == 0):
            try:
                print ("No solution has been found for match with id {}!".format(self.match["id"]))
            except:
                print ("Match format error!")
        else:
            print ("The best solution for match with id {} has a profit of {}%.".format(self.match["id"], (1.0 - self.bestPrice) * 100))
            print ("The solution consists of the following bets:")
            for type_id in self.bestBet:
                print (type_id, self.bestBet[type_id])

    def getBestBet(self):
        return self.bestBet

from time import sleep
from datetime import datetime, timedelta
from BetAPI.oddfeedsApi import *
from BetAPI.model import Match
from BetAPI.config import *
def surebet_thread(db, cache):
    last_prematch_update = None
    session = db.create_scoped_session()

    #sleep(LIVE_UPDATE_INTERVAL) # delay before start
    while True:
        to_update = []
        now = datetime.utcnow()
        if last_prematch_update == None or last_prematch_update + timedelta(minutes=PREMATCH_UPDATE_INTERVAL) < now:
            matches = session.query(Match).filter((Match.time > now) & (Match.time < (now + timedelta(minutes=AHEAD_INTERVAL)))).all()
            last_prematch_update = now
            for m in matches:
                to_update.append(m.id)

        matches = session.query(Match).filter(Match.live & (Match.time > now) & (Match.time < (now + timedelta(minutes=AHEAD_INTERVAL)))).all()
        for m in matches:
            to_update.append(m.id)

        to_update = [to_update[i:i+25] for i in range(0, len(to_update), 25)]
        to_change = {}
        for ids in to_update:
            data = getOddsForMatches(ids, TARGET_BOOKMAKERS, TARGET_ODDS)
            for odd in data["odds"]["prematch"]:
                if odd["match_id"] in to_change.keys():
                    to_change[odd["match_id"]].append(odd)
                else:
                    to_change[odd["match_id"]] = [odd]
            for odd in data["odds"]["inplay"]:
                if odd["match_id"] in to_change.keys():
                    to_change[odd["match_id"]].append(odd)
                else:
                    to_change[odd["match_id"]] = [odd]

            for k in to_change.keys():
                cache[k] = to_change[k]

        surebets = []
        for m in cache.keys():
            if m == "surebets": continue
            obj = {
                "id": m,
                "odds": cache[m]
            }

            b = BetFinder(obj, TARGET_BETS)
            sol = b.getBestBet()
            b.printBestBet()
            if sol != {}:
                for k in sol.keys():
                    print ("{}-{}: Price={} Bookmaker={} HC={}".format(sol[k]['match_id'], k, sol[k]['price'], sol[k]['bookmaker']['name'], sol[k]['hc']))
                print ("------------------------------------")
                sol[-1] = session.query(Match).filter(Match.id == m).first().json
                surebets.append(sol)
 


        cache["surebets"] = surebets
        sleep(LIVE_UPDATE_INTERVAL)
