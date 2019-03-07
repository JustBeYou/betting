"""A custom API blueprint.

This api module is *additional* to the CRUD API exposed by Flask-Restless. It
should be used only when a custom, non-CRUD, API is necessary.

"""

from flask import Blueprint, request, redirect
from oddfeedsApi import *
from model import db
from json import loads
from pprint import pprint
from time import time, sleep
from datetime import datetime, timedelta
from threading import Thread
import sqlite3

api = Blueprint('api', __name__, template_folder='templates')
