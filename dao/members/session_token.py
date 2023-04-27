from datetime import datetime

from ..database_model import DatabaseModel

class SessionToken(DatabaseModel):
    __tablename__ = "session_tokens"
    __primary__ = "token_id"

    token_id : int = None
    member_id : int

    token : str
    last_used : datetime = "CURRENT_TIMESTAMP"