import json
import os
import re

from dotenv import load_dotenv

import mysql.connector.pooling

load_dotenv()

# Constants
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

STRONG_PASSWORD_REG = re.compile(r"^(?=.*[A-Z])(?=.*)(?=.*[0-9])(?=.*[a-z]).{8,}$")
EMAIL_REG = re.compile(r"[\w\.-]+@[\w\.-]+(\.[\w]+)+")

# Load files
with open("email_verification.html", "r") as f: EMAIL_VERIFICATION_MESSAGE = f.read()
with open("static/countries.json", "r") as f: COUNTRIES : dict = json.load(f)
with open("config.json", "r") as f: CONFIG : dict = json.load(f)

# Initilize MySQL

cnx_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_size=CONFIG["mysql_pool_size"],
    user=os.getenv("MYSQL_DATABASE_USER"),
    password=os.getenv("MYSQL_DATABASE_PASSWORD"),
    host=os.getenv("MYSQL_DATABASE_HOST"),
    database=os.getenv("MYSQL_DATABASE_DB")
)

class BaseType:
    def __init__(self, value): self._value = value
    
    def __str__(self) -> str: return str(self._value)
    def __eq__(self, to): return self._value == to