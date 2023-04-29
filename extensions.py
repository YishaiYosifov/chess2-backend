import json
import os
import re

from dotenv import load_dotenv

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

class BaseType:
    def __init__(self, value):
        self.types = [type(self)]

        if isinstance(value, BaseType):
            self._value = value._value
            self.types += value.types
        else:
            self.statement = {"value": value}