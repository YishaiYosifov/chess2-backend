from unittest.mock import _patch, patch
from datetime import datetime
from types import ModuleType

from pytest_mock import MockerFixture
from fastapi import FastAPI

from app.models.user_model import User
from app.crud import user_crud
from app import deps

from .dep_overrider import DependencyOverrider


def mock_hash() -> _patch:
    return patch.object(
        user_crud.auth_service,
        "hash_password",
        return_value="$2b$12$kXC0QfbIfmjauYXOp9Hoj.ehDU1mWXgvTCvxlTVfEKyf35lR71Fam",
    )


def mock_login(
    app: FastAPI, user: User, *class_args, **class_kwargs
) -> DependencyOverrider:
    """
    Creates a context where the user is logged in.
    This is faster than sending a request to /auth/login because it doesn't actually generate a hash.

    :param user: a user object to mock login into
    """

    override_authed_user = DependencyOverrider(
        app,
        overrides={deps.AuthedUser(*class_args, **class_kwargs): lambda: user},
    )
    return override_authed_user


def me_login(app: FastAPI, user: User) -> DependencyOverrider:
    """
    Creates a context where `/me` routes recognize the user as logged in
    This is faster than sending a request to /auth/login because it doesn't actually generate a hash.

    :param user: a user object to mock login into
    """

    override_me_user = DependencyOverrider(
        app,
        overrides={deps.TargetOrMeDep: lambda: user},
    )
    return override_me_user


def fix_time(
    module: ModuleType,
    mocker: MockerFixture,
    to: datetime | None = None,
) -> tuple[datetime, int]:
    fixed_datetime = to or datetime(2023, 6, 9)
    fixed_timestamp = int(fixed_datetime.timestamp())

    if hasattr(module, "time"):
        mocker.patch.object(module.time, "time", return_value=fixed_timestamp)

    if hasattr(module, "datetime"):
        mock_datetime = mocker.patch.object(module, "datetime")
        mock_datetime.utcnow = mocker.Mock(return_value=fixed_datetime)

    return fixed_datetime, fixed_timestamp
