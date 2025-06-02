from flask import Flask
import pymongo
from flask_bcrypt import Bcrypt


#initializing app
app = Flask(__name__)
app.secret_key = "secret_secret_secret"

#connecting to mongodb cluster and database
cluster = pymongo.MongoClient("mongodb://localhost:27017/")
db = cluster.sh_app

bcrypt = Bcrypt()

from sb import routes