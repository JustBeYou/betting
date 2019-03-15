from requests import get
from BetManager.config import *

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
ODD_TYPES_IDS = dict((v,k) for k,v in ODD_TYPES.items())

BOOKMAKERS = {
    "Bet365": 26,
    "Pinnacle": 10,
    "1xBet": 55
}
BOOKMAKERS_IDS = dict((v,k) for k,v in BOOKMAKERS.items())


def getMatches():
    return get(API_URL + 'matches').json()

def getSureBets():
    return get(API_URL + 'surebets').json()
