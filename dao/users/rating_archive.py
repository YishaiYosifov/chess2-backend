from app import db

class RatingArchive(db.Model):
    __tablename__ = "rating_archive"

    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    user = db.relationship("User", uselist=False)

    mode = db.Column(db.String(50))
    elo = db.Column(db.Integer, server_default=db.text("800"))

    achieved_at = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))