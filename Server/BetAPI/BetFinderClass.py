# module for finding the best sure bet for a match.
# author: Gabi Tulba
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
        __findBestOdds()

    def __getBestHandicap(self):
        for period in self.bestHCSol:
            for hc in self.bestHCSol[period]:
                try:
                    for sureBet in handicapSureBets:
                        current = {}
                        priceSum = 0.0
                        for type_id in sureBet:
                            current[type_id] = self.bestHCSol[period][hc][type_id]
                            priceSum += 1.0 / current[type_id]["price"]
                        if len(current) == len(sureBet):
                            if priceSum < self.bestHCPrice:
                                self.bestHCPrice = priceSum
                                self.bestHCBet = current
                except:
                    continue

    def __getBestClassic(self):
        for period in self.bestSol:
                try:
                    for sureBet in SureBets:
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
                if "hc" in odd:
                    if not odd["period_id"] in self.bestHCSol:
                        self.bestHCSol[odd["period_id"]] = {}
                    if not odd["hc"] in self.bestHCSol[odd["period_id"]]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]] = {}
                    if not odd["type_id"] in self.bestHCSol[odd["period_id"]][odd["hc"]]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]] = {odd["type_id"]: odd}
                    elif odd["price"] > self.bestHCSol[odd["period_id"]][odd["hc"]][odd["type_id"]]["price"]:
                        self.bestHCSol[odd["period_id"]][odd["hc"]][odd["type_id"]] = odd
                else:
                    if not odd["period_id"] in self.bestSol:
                        self.bestSol[odd["period_id"]] = {}
                        if not odd["type_id"] in self.bestSol[odd["period_id"]]:
                            self.bestSol[odd["period_id"]][odd["type_id"]] = odd
                        elif odd["price"] > self.bestBets[odd["period_id"]][odd["type_id"]]["price"]:
                            self.bestBets[odd["period_id"]][odd["type_id"]] = odd
            if(self.handicap):
                __getBestHandicap()
            __getBestClassic()
            
            if len(self.bestHCBet) != 0:
                self.finalBet = self.bestHCBet
                self.finalPrice = self.bestHCPrice
            if len(self.bestBet) != 0:
                if self.finalPrice > self.bestPrice:
                    self.finalBet = self.bestBet
                    self.finalPrice = self.bestPrice
 
        except:
            print "Match format error!"

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
