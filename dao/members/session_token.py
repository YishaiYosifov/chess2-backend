from app import db

class SessionToken(db.Model):
    __tablename__ = "session_tokens"
    
    token_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.member_id"))

    token = db.Column(db.Text)
    last_used = db.Column(db.DateTime, default=db.func.current_timestamp())