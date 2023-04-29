from app import db

class OutgoingGame(db.Model):
    __tablename__ = "outgoing_games"

    outgoing_game_id = db.Column(db.Integer, primary_key=True)
    
    member_id = db.Column(db.Integer, db.ForeignKey("members.member_id"))

    mode = db.Column(db.String(50))
    time_control = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_pool = db.Column(db.Boolean, default=False)