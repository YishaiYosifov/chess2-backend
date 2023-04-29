from app import db

class Rating(db.Model):
    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.member_id"))

    mode = db.Column(db.String(50))
    elo = db.Column(db.Integer, default=800)