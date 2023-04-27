from datetime import datetime

from .database_model import DatabaseModel

class EmailVerification(DatabaseModel):
    __tablename__ = "email_verifications"
    __primary__ = "verification_id"

    verification_id : int = None
    member_id : int

    token : str
    created_at : datetime = "CURRENT_TIMESTAMP"