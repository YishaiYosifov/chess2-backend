from datetime import datetime
from typing import Annotated
from http import HTTPStatus

from fastapi import APIRouter, Query

from app.schemas.response_schema import ErrorResponse
from app.constants import enums
from app.schemas import user_schema, game_schema
from app.crud import ratings_crud, game_crud
from app import deps

router = APIRouter(prefix="/profile", tags=["profile"])

user_not_found_response = {
    HTTPStatus.NOT_FOUND: {
        "description": "Target user not found",
        "model": ErrorResponse[str],
    }
}


@router.get(
    "/{target}/info",
    response_model=user_schema.UserOut,
    responses={**user_not_found_response},
)
def get_info(target: deps.TargetOrMeDep):
    return target


@router.get("/me/info-sensitive", response_model=user_schema.UserOutSensitive)
def get_info_sensitive(user: deps.AuthedUserDep):
    return user


@router.get(
    "/{target}/games",
    response_model=list[game_schema.GameResults],
    responses={**user_not_found_response},
)
def get_games(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    limit: Annotated[int, Query(le=100, gt=0)],
):
    return game_crud.fetch_history(
        db,
        target,
        limit,
    )


@router.get(
    "/{target}/ratings",
    response_model=dict[enums.Variant, game_schema.Rating],
    responses={**user_not_found_response},
)
def get_ratings(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    variants: Annotated[list[enums.Variant], Query()],
):
    return ratings_crud.fetch_many(db, target, variants)


@router.get("/{target}/rating_history", responses={**user_not_found_response})
def get_ratings_history(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    variants: Annotated[list[enums.Variant], Query()],
    since: datetime,
):
    # TODO
    pass
