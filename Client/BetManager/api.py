from flask import Blueprint, request, redirect
from BetManager.model import db, Match
import BetManager.bot
from json import loads
from pprint import pprint
from time import time, sleep
from datetime import datetime, timedelta
from threading import Thread
import sqlite3

api = Blueprint('api', __name__, template_folder='templates')
