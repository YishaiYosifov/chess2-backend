from app import db

class OutgoingGames(db.Model):
    __tablename__ = "outgoing_games"

    outgoing_game_id = db.Column(db.Integer, primary_key=True)
    
    inviter_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    game_settings_id = db.Column(db.Integer, db.ForeignKey("game_settings.game_settings_id"))
    game_settings = db.relationship("GameSettings", uselist=False)

    created_at = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))
    is_pool = db.Column(db.Boolean, server_default=db.text("FALSE"))