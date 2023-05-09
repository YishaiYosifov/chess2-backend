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

# Pieces movement
straight_movement = lambda origin, destination: origin["x"] == destination["x"] or origin["y"] == destination["y"]
diagonal_movement = lambda origin, destination: abs(origin["x"] - destination["x"]) == abs(origin["y"] - destination["y"])
knight_movement = lambda origin, destination: (abs(origin["y"] - destination["y"]) == 2 and abs(origin["x"] - destination["x"]) == 1) or \
                                                (abs(origin["y"] - destination["y"]) == 1 and abs(origin["x"] - destination["x"]) == 2)

PIECE_MOVEMENT = {
    "rook": {
        "move": {
            "validator": straight_movement,
            "collisions": ["straight"]
        }
    },
    "bishop": {
        "move": {
            "validator": diagonal_movement,
            "collisions": ["diagonal"]
        }
    },
    "knight": {
        "move": {
            "validator": knight_movement
        }
    },
    "king": {
        "move": {
            "validator": lambda origin, destination: abs(origin["y"] - destination["y"]) <= 1 and abs(origin["x"] - destination["x"]) <= 1,
            "collisions": ["straight", "diagonal"]
        }
    },
    "queen": {
        "move": {
            "validator": straight_movement or diagonal_movement,
            "collisions": ["straight", "diagonal"]
        }
    },
    "diagook": {
        "move": {
            "validator": straight_movement,
            "collisions": ["straight"]
        },
        "capture": {
            "validator": diagonal_movement,
            "collisions": ["diagonal"]
        }
    },
    "archbishop": {
        "move": {
            "validator": diagonal_movement,
            "collisions": ["diagonal"]
        },
        "capture": {
            "validator": straight_movement,
            "collisions": ["straight"]
        }
    },
    "knook": {
        "move": {
            "validator": straight_movement,
        },
        "capture": {
            "validator": knight_movement
        }
    },
    "pawn": {
        "move": {
            "validator": lambda origin, destination: origin["x"] == destination["x"] and destination["y"] - origin["y"] == 1,
            "collisions": ["straight"]
        },
        "capture": {
            "validator": lambda origin, destination: abs(origin["y"] - destination["y"]) == 1 and origin["x"] != destination["x"]
        },
    },
    "child_pawn": {
        "move": {
            "validator": lambda origin, destination: origin["x"] == destination["x"] and destination["y"] - origin["y"] == 1,
            "collisions": ["straight"]
        }
    }
}