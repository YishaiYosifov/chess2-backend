from sqlalchemy.ext.hybrid import hybrid_property
from app import db

class Player(db.Model):
    __tablename__ = "players"

    player_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    user = db.relationship("User", backref="player_in", uselist=False)
    color = db.Column(db.Text(10))

    score = db.Column(db.Integer, server_default=db.text("0"))
    clock_synced_since_last_turn_at = db.Column(db.Double, server_default=db.text("(UNIX_TIMESTAMP())"))
    clock = db.Column(db.Double)

    @hybrid_property
    def game(self): return self.game_white or self.game_black

    def __eq__(self, to):
        from ..users.user import User
        if not isinstance(to, User) and not isinstance(to, Player): return False
        return to.user_id == self.user_id