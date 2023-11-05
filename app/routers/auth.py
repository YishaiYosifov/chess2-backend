from typing import Annotated
from http import HTTPStatus

from fastapi import HTTPException, APIRouter, Body

from app.crud.user_crud import fetch_user_by_selector, create_user
from app.schemes.user import UserIn
from app.dependencies import SettingsDep, DBDep

router = APIRouter(tags=["auth"], prefix="/auth")


@router.post("/register")
async def register(user: Annotated[UserIn, Body()], db: DBDep, settings: SettingsDep):
    """
    Takes a username, email and password and creates a credentials user.
    This function will also
        - send a verification email
        - set the user's country of origin to the ip origin
        - create the necessary files
    """

    if await fetch_user_by_selector(db, user.username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"username": "Username Taken"},
        )

    db_user = create_user(db, user)

    try:
        send_verification_email(user)
    except GoogleAPIError:
        pass

    await db.commit()

    return success_response(status=HTTPStatus.CREATED)
