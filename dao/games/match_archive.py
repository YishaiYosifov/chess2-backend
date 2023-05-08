from app import db

class MatchArchive(db.Model):
    __tablename__ = "match_archives"

    game_archive_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)
    
    white_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    black_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    white = db.relationship("User", foreign_keys=[white_id], uselist=False)
    black = db.relationship("User", foreign_keys=[black_id], uselist=False)

    winner = db.Column(db.String(10))

    game_settings_id = db.Column(db.Integer, db.ForeignKey("game_settings.game_settings_id"))
    game_settings = db.relationship("GameSettings", uselist=False)

    moves = db.Column(db.Text, server_default=db.text("('')"))
    white_wins = db.Column(db.Integer, server_default=db.text("0"))
    black_wins = db.Column(db.Integer, server_default=db.text("0"))