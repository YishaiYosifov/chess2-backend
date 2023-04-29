import os

from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from dotenv import load_dotenv

import urllib.parse
import flask

load_dotenv()

app = flask.Flask(__name__)
app.secret_key = "bb5c8af0e15d4d0195e37fa995430280"

DB_USERNAME = os.getenv("MYSQL_DATABASE_USER")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("MYSQL_DATABASE_PASSWORD"))
DB_HOST = os.getenv("MYSQL_DATABASE_HOST")
DB_DATABASE = os.getenv("MYSQL_DATABASE_DB")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}"

db = SQLAlchemy(app)
socketio = SocketIO(app)