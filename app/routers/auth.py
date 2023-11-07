from http import HTTPStatus

from fastapi import BackgroundTasks, HTTPException, APIRouter

from app.utils.email_verification import send_verification_email
from app.schemes.responses import ConflictResponse
from app.utils.user_setup import setup_user
from app.schemes.user import UserOut, UserIn
from app.dependencies import SettingsDep, DBDep
from app.crud import user_crud

router = APIRouter(tags=["auth"], prefix="/auth")


@router.post(
    "/signup",
    response_model=UserOut,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CONFLICT: {
            "description": "Username / email already taken",
            "model": ConflictResponse,
        }
    },
)
def signup(
    user: UserIn,
    db: DBDep,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
):
    """
    Takes a username, email and password and creates registers a new user.

    This path operation will also:
    - send a verification email
    - create the necessary files
    """

    if user_crud.fetch_user_by_selector(db, user.username):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"username": "Username taken"},
        )
    elif user_crud.fetch_user_by_selector(db, user.email):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={"email": "Email taken"},
        )

    db_user = user_crud.create_user(db, user)
    if settings.send_verification_email:
        background_tasks.add_task(send_verification_email, user=db_user)

    setup_user(db, db_user)

    return db_user
