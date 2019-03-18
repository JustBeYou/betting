AHEAD_INTERVAL = 1 * 120 # minutes
PREMATCH_UPDATE_INTERVAL = 3 # minutes
LIVE_UPDATE_INTERVAL = 30 # seconds
MATCH_LIFETIME = 100 # minutes
MATCH_LIST_UPDATE_INTERVAL = 30 # minutes

from BetAPI.oddfeedsApi import BOOKMAKERS, ODD_TYPES
TARGET_BOOKMAKERS = [
    BOOKMAKERS["1xBet"],
    BOOKMAKERS["Pinnacle"],
    #BOOKMAKERS["BetfairExchange"]
    #BOOKMAKERS["Bet365"]
]
TARGET_ODDS = [
    ODD_TYPES["1"],
    ODD_TYPES["X"],
    ODD_TYPES["2"],
    ODD_TYPES["1X"],
    ODD_TYPES["X2"],
    ODD_TYPES["Over"],
    ODD_TYPES["Under"]
]
TARGET_BETS = [
    [ODD_TYPES["1"], ODD_TYPES["X"], ODD_TYPES["2"]],
    [ODD_TYPES["1X"], ODD_TYPES["2"]],
    [ODD_TYPES["1"], ODD_TYPES["X2"]],
]
TARGET_BETS_HC = [
    [ODD_TYPES["Over"], ODD_TYPES["Under"]]
]

DEBUG_FAKE_SUREBET = True
