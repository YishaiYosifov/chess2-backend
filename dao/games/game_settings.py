from app import db

class GameSettings(db.Model):
    __tablename__ = "game_settings"

    game_settings_id = db.Column(db.Integer, primary_key=True)

    mode = db.Column(db.String(15))
    time_control = db.Column(db.Integer)
    increment = db.Column(db.Integer)