from contextlib import contextmanager
from datetime import datetime
from typing import Generator
from types import ModuleType

from pytest_mock import MockerFixture
from fastapi import FastAPI
from pytest import MonkeyPatch

from app.models.user_model import AuthedUser, User
from app import deps

from .dep_overrider import DependencyOverrider


@contextmanager
def mock_login(user: User) -> Generator:
    """
    Creates a context where the user is logged in.
    This is faster than sending a request to /auth/login because it doesn't actually generate a hash.

    This overrides every parameter the GetCurrentUser dependency could get by monkeypatching the __call__ method.

    :param user: a user object to mock login into
    """

    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(deps.GetCurrentUser, "__call__", lambda self: user)
        yield


def me_login(app: FastAPI, user: AuthedUser) -> DependencyOverrider:
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
