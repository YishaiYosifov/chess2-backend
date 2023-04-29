from app import db

class EmailVerification(db.Model):
    __tablename__ = "email_verifications"

    verification_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.member_id"))

    token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())