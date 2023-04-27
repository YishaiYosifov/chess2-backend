from flask_socketio import SocketIO
import flask

app = flask.Flask(__name__)
app.secret_key = "bb5c8af0e15d4d0195e37fa995430280"
socketio = SocketIO(app)