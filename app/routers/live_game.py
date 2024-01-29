from fastapi import APIRouter

from app.schemas import game_schema
from app.crud import live_game_crud
from app import deps

router = APIRouter(prefix="/live-game", tags=["live-game"])


@router.get("/", response_model=game_schema.LiveGame)
def get_live_game(db: deps.DBDep):
    return live_game_crud.fetch_live_game(db, "5e098f15")
