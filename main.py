import flask

from member import *
from util import *

app = flask.Flask(__name__)

@app.route("/test")
@requires_authentication(type=Player, allow_guests=True)
def test(user : Player):
    print(user)
    return "ok", 200

if __name__ == "__main__": app.run("0.0.0.0", debug=True)