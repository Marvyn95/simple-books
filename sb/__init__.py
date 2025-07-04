from flask import Flask
import pymongo
from flask_bcrypt import Bcrypt
import json

with open("../config.json") as config_file:
    config = json.load(config_file)

#initializing app
app = Flask(__name__)
app.secret_key = config.get("SECRET_KEY")
#connecting to mongodb cluster and database
cluster = pymongo.MongoClient(config.get("CONNECTION_STRING"))
db = cluster.sb_app

bcrypt = Bcrypt()

from sb import routes