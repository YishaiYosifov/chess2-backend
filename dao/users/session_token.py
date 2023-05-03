from app import db

class SessionToken(db.Model):
    __tablename__ = "session_tokens"
    
    token_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))

    token = db.Column(db.Text)
    last_used = db.Column(db.DateTime, server_default=db.text("(UTC_TIMESTAMP)"))