from app import db

class EmailVerification(db.Model):
    __tablename__ = "email_verifications"

    verification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))