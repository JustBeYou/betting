AHEAD_INTERVAL = 120 # minutes
PREMATCH_UPDATE_INTERVAL = 30 # minutes
LIVE_UPDATE_INTERVAL = 60 # seconds
MATCH_LIFETIME = 100 # minutes
MATCH_LIST_UPDATE_INTERVAL = 60 # minutes

from BetAPI.oddfeedsApi import BOOKMAKERS, ODD_TYPES
TARGET_BOOKMAKERS = [
    BOOKMAKERS["1xBet"],
    BOOKMAKERS["Pinnacle"],
    BOOKMAKERS["Bet365"]
]
TARGET_ODDS = [
    ODD_TYPES["1"],
    ODD_TYPES["X"],
    ODD_TYPES["2"],
    ODD_TYPES["Over"],
    ODD_TYPES["Under"]
]
TARGET_BETS = [
    [ODD_TYPES["1"], ODD_TYPES["X"], ODD_TYPES["2"]]
    #[ODD_TYPES["Over"], ODD_TYPES["Under"]]
]
