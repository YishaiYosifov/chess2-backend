from app import db

class Match(db.Model):
    __tablename__ = "matches"

    match_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)

    games = db.relationship("Game", backref="match")

    white_results = db.Column(db.Integer, server_default=db.text("0"))
    black_results = db.Column(db.Integer, server_default=db.text("0"))

    is_active = db.Column(db.Boolean, server_default=db.text("TRUE"))
    last_game_over = db.Column(db.DateTime, server_default=db.text("NULL"))