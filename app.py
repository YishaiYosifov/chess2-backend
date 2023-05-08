from datetime import timedelta

import os

from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_session import Session
from dotenv import load_dotenv

import urllib.parse
import flask

from extensions import CONFIG

load_dotenv()

app = flask.Flask(__name__)

DB_USERNAME = os.getenv("MYSQL_DATABASE_USER")
DB_PASSWORD = urllib.parse.quote_plus(os.getenv("MYSQL_DATABASE_PASSWORD"))
DB_HOST = os.getenv("MYSQL_DATABASE_HOST")
DB_DATABASE = os.getenv("MYSQL_DATABASE_DB")
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}"

app.config["SQLALCHEMY_POOL_SIZE"] = CONFIG["MYSQL_POOL_SIZE"]
app.config["SQLALCHEMY_MAX_OVERFLOW"] = CONFIG["MYSQL_MAX_OVERFLOW"]

db = SQLAlchemy(app)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = "bb5c8af0e15d4d0195e37fa995430280"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(weeks=2)
Session(app)

socketio = SocketIO(app, manage_session=False)