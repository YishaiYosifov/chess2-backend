from http import HTTPStatus

from fastapi import HTTPException, APIRouter

from app.schemas import response_schema, game_schema
from app.crud import game_crud
from app import deps

router = APIRouter(prefix="/live-game", tags=["live-game"])


@router.get(
    "/",
    response_model=game_schema.LiveGame,
    responses={
        HTTPStatus.NOT_FOUND: {
            "description": "Game Not Found",
            "model": response_schema.ErrorResponse[str],
        }
    },
)
def get_live_game(db: deps.DBDep, token: str):
    """Fetch everything neccasary to load a game"""

    game = game_crud.fetch_live_game(db, token)
    if not game:
        raise HTTPException(HTTPStatus.NOT_FOUND, "Game Not Found")

    return game
