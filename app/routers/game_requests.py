from http import HTTPStatus

from fastapi import HTTPException, APIRouter, Response

from app.services import game_request_service
from app.schemas import response_schema, game_schema
from app import deps

router = APIRouter(prefix="/game-requests", tags=["game-requests"])


@router.post(
    "/pool/join",
    responses={
        HTTPStatus.CONFLICT: {
            "description": "You already have an active game",
            "model": response_schema.ErrorResponse[str],
        },
        HTTPStatus.CREATED: {"description": "Entered the pool"},
        HTTPStatus.OK: {"description": "Game started"},
    },
)
def start_pool_game(
    db: deps.DBDep,
    user: deps.UnauthedUserDep,
    game_settings: game_schema.GameSettings,
):
    """
    Joins the matchmaking pool with the specified game settings.
    If a game was not found, it will create a new game request.
    """

    if user.game:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="You already have an active game",
        )
    elif user.game_request:
        db.delete(user.game_request)
        db.flush()

    token = game_request_service.create_or_start_pool_game(
        db, user, game_settings
    )
    db.commit()

    # If a token is returned, it means the game started so return the token.
    # If None was returned, it means a new game request was created so return CREATED
    return (
        Response(content=token, status_code=HTTPStatus.OK)
        if token
        else Response(status_code=HTTPStatus.CREATED)
    )
