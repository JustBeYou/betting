from API import *
from pprint import pprint

bks = [
    BOOKMAKERS["Pinnacle"]
]
tps = [
    ODD_TYPES["1"],
    ODD_TYPES["X"],
    ODD_TYPES["2"]
]
data = getData(bks, tps)
import json
with open('data.json', 'w') as outfile:
    json.dump(data, outfile)

print ("Found {} matches".format(len(data['matches'])))
print ("Found {} inplay odds and {} prematch odds".format(len(data['odds']['inplay']), len(data['odds']['prematch'])))
