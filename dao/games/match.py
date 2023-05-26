from app import db

class Match(db.Model):
    __tablename__ = "matches"

    match_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)

    games = db.relationship("Game", backref="match")

    white_score = db.Column(db.Integer, server_default=db.text("0"))
    black_score = db.Column(db.Integer, server_default=db.text("0"))