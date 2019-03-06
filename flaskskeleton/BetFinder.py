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
				print "No solution has been found for match with id {}!".format(self.match["id"])
			except:
				print "Match format error!"
		else:
			print "The best solution for match with id {} has a profit of {}%.".format(self.match["id"], (1.0 - self.bestPrice) * 100)
			print "The solution consists of the following bets:"
			for type_id in self.bestBet:
				print type_id, self.bestBet[type_id]

	def getBestBet(self):
		return self.bestBet
