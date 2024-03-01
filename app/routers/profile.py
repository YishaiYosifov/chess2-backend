from datetime import timedelta, datetime, date
from typing import Annotated
from http import HTTPStatus
import os

from fastapi.responses import FileResponse
from fastapi import HTTPException, APIRouter, Query

from app.constants import enums
from app.schemas import response_schema, user_schema, game_schema
from app.crud import rating_crud, game_crud
from app import deps

router = APIRouter(prefix="/profile", tags=["profile"])

user_not_found_response = {
    HTTPStatus.NOT_FOUND: {
        "description": "Target user not found",
        "model": response_schema.ErrorResponse[str],
    }
}


@router.get(
    "/{target}/info",
    response_model=user_schema.AuthedProfileOut,
    responses={**user_not_found_response},
)
def get_info(target: deps.TargetOrMeDep):
    """Fetch a user's profile"""
    return target


@router.get(
    "/me/info-sensitive",
    response_model=user_schema.PrivateAuthedProfileOut,
)
def get_info_sensitive(user: deps.AuthedUserDep):
    """Fetch the sensitive profile of user"""
    return user


@router.get(
    "/{target}/games",
    response_model=list[game_schema.FinishedGame],
    responses={**user_not_found_response},
)
def paginate_games(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    page: int = 0,
    per_page: Annotated[int, Query(le=10, gt=0, alias="per-page")] = 10,
):
    """
    Paginate through game history for a specified target.
    Retrieve a paginated list of game results.
    """

    return game_crud.paginate_history(db, target, page, per_page)


@router.get(
    "/{target}/total-game-count",
    response_model=int,
    responses={**user_not_found_response},
)
def total_game_count(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
):
    """Count how many games a user has"""

    return game_crud.total_count(db, target)


@router.get(
    "/{target}/ratings",
    response_model=dict[enums.Variant, game_schema.Rating],
    responses={**user_not_found_response},
)
def get_ratings(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    variants: Annotated[list[enums.Variant], Query()] = list(enums.Variant),
):
    """
    Get the current ratings of a user.
    If a user is unrated in a certain variant, that variant will not be returned.
    """

    return rating_crud.fetch_many(db, target, variants)


@router.get(
    "/{target}/rating-history",
    response_model=dict[enums.Variant, game_schema.RatingOverview],
    responses={
        **user_not_found_response,
        HTTPStatus.BAD_REQUEST: {
            "description": "Bad 'since' value",
            "model": response_schema.ErrorResponse[dict[str, str]],
        },
    },
)
def get_ratings_history(
    db: deps.DBDep,
    target: deps.TargetOrMeDep,
    since: date,
    variants: Annotated[list[enums.Variant], Query()] = list(enums.Variant),
):
    """
    Get the rating history of a user.
    If a user is unrated in a certain variant, that variant will not be returned.
    """

    # Make sure the `since` date is valid
    now = datetime.utcnow().date()
    if since < now - timedelta(days=60):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"since": "cannot be more than 2 months in the past"},
        )
    elif since > now:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={"since": "cannot be in the future"},
        )

    history = rating_crud.fetch_history(db, target, since, variants)
    minmax = rating_crud.fetch_min_max(db, target, variants)

    # Merge the history and min max values together
    results = {
        variant: {
            "min": minmax[variant][0],
            "max": minmax[variant][1],
            "current": history[variant][-1].elo,
            "history": history[variant],
        }
        for variant in variants
        if history.get(variant) and minmax.get(variant)
    }
    return results


@router.get(
    "/{target}/profile-picture",
    response_class=FileResponse,
    responses={HTTPStatus.OK: {"content": {"image/webp": {}}}},
)
async def profile_picture(target: deps.TargetOrMeDep):
    """
    Get a user's profile picture.
    If the user hasn't uploaded a picture yet, the default one will be returned.
    """

    uploads_path = f"uploads/{target.user_id}/profile-picture.webp"
    if os.path.exists(uploads_path):
        return FileResponse(
            f"uploads/{target.user_id}/profile-picture.webp",
            media_type="image/webp",
        )

    return FileResponse(
        "assets/default-profile-picture.webp",
        media_type="image/webp",
    )
