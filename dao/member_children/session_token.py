from pydantic import BaseModel

from .. import DatabaseModel

class SessionToken(BaseModel, DatabaseModel):
    _table = "session_tokens"
    _primary = "token_id"

    token_id : int = None
    member_id : int

    token : str
    create_at : int