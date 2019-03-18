import logging

class BetFinder:
    def __init__(self, match, sureBets = {}, handicap = False, handicapSureBets = {}):
        self.match = match
        self.handicap = handicap
        self.sureBets = sureBets
        self.handicapSureBets = handicapSureBets
        self.bestHCSol = {}
        self.bestSol = {}
        self.bestBet = {}
        self.bestPrice = 1.0
        self.bestHCBet = {}
        self.bestHCPrice = 1.0
        self.finalBet = {}
        self.finalPrice = 1.0
        self.__findBestOdds()

    def __getBestHandicap(self):
        for period in self.bestHCSol:
            for hc in self.bestHCSol[period]:
                try:
                    for sureBet in self.handicapSureBets:
                        current = {}
                        priceSum = 0.0
                        for type_id in sureBet:
                            current[type_id] = self.bestHCSol[period][hc][type_id]
                            priceSum += 1.0 / current[type_id]["price"]
                        if len(current) == len(sureBet):
                            if priceSum < self.bestHCPrice or DEBUG_FAKE_SUREBET:
                                self.bestHCPrice = priceSum
                                self.bestHCBet = current
                except:
                    continue

    def __getBestClassic(self):
        for period in self.bestSol:
                try:
                    for sureBet in self.sureBets:
                        current = {}
                        priceSum = 0.0
                        for type_id in sureBet:
                            current[type_id] = self.bestSol[period][type_id]
                            priceSum += 1.0 / current[type_id]["price"]
                        if len(current) == len(sureBet):
                            if priceSum < self.bestPrice:
                                self.bestPrice = priceSum
                                self.bestBet = current
                except:
                    continue

    def __findBestOdds(self):
        try:
            for odd in self.match["odds"]:
                if odd["hc"] - int(odd["hc"]) == 0.25 or \
                   odd["hc"] - int(odd["hc"]) == 0.75:
                       continue

                if odd["hc"] != 0 :
                    if not odd["period_id"] in self.bestHCSol:
                        self.bestHCSol[odd["period_id"]] = {}
                    if not odd["hc"] in self.bestHCSol[odd["period_id"]]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]] = {}
                    if not odd["type_id"] in self.bestHCSol[odd["period_id"]][odd["hc"]]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]][odd["type_id"]] = odd
                    elif odd["price"] > self.bestHCSol[odd["period_id"]][odd["hc"]][odd["type_id"]]["price"]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]][odd["type_id"]] = odd
                else:
                    if not odd["period_id"] in self.bestSol:
                        self.bestSol[odd["period_id"]] = {}
                    if not odd["type_id"] in self.bestSol[odd["period_id"]]:
                        self.bestSol[odd["period_id"]][odd["type_id"]] = odd
                    elif odd["price"] > self.bestSol[odd["period_id"]][odd["type_id"]]["price"]:
                        self.bestSol[odd["period_id"]][odd["type_id"]] = odd
            if(self.handicap):
                self.__getBestHandicap()
            self.__getBestClassic()

            if len(self.bestHCBet) != 0:
                self.finalBet = self.bestHCBet
                self.finalPrice = self.bestHCPrice
            if len(self.bestBet) != 0:
                if self.finalPrice > self.bestPrice or DEBUG_FAKE_SUREBET:
                    self.finalBet = self.bestBet
                    self.finalPrice = self.bestPrice

        except:
            logging.info("Match format error!")

    def printBestBet(self):
        if(len(self.finalBet) == 0):
            try:
                print ("No solution has been found for match with id {}!".format(self.match["id"]))
            except:
                print ("Match format error!")
        else:
            print ("The best solution for match with id {} has a profit of {}%.".format(self.match["id"], (1.0 - self.finalPrice) * 100))
            print ("The solution consists of the following bets:")
            for type_id in self.finalBet:
                print (type_id, self.finalBet[type_id])

    def getBestBet(self):
        return self.finalBet

    def getProfit(self):
        return "{:.2f}".format((1.0 - self.finalPrice) * 100)


from time import sleep, time
from datetime import datetime, timedelta
from BetAPI.oddfeedsApi import *
from BetAPI.model import Match
from BetAPI.config import *
def surebet_thread(db, cache):
    last_prematch_update = None
    session = db.create_scoped_session()

    while True:
        start_time = time()

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

            b = BetFinder(obj, TARGET_BETS, True, TARGET_BETS_HC)
            sol = b.getBestBet()
            if sol != {}:
                surebets.append({
                    "match": session.query(Match).filter(Match.id == m).first().json,
                    "profit": b.getProfit(),
                    "odds": sol
                    })
        cache["surebets"] = surebets

        logging.info("Surebet calculator took {:.2}s".format(time() - start_time))
        sleep(LIVE_UPDATE_INTERVAL)
