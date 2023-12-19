from datetime import timedelta, datetime
from typing import Any
from http import HTTPStatus
from abc import abstractmethod, ABC

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services import auth_service
from app.utils import email_verification
from app.crud import user_crud
from app.db import Base

from ..models.user_model import AuthedUser


class Setting(ABC):
    def __init__(self, user: AuthedUser) -> None:
        self.user = user

    @abstractmethod
    def update(self, value: str) -> None:
        pass


class PasswordSetting(Setting):
    def update(self, new_password: str) -> None:
        hashed_password = auth_service.hash_password(new_password)
        self.user.hashed_password = hashed_password


class ValidationSetting(Setting, ABC):
    def __init__(self, db: Session, user: AuthedUser) -> None:
        self.user = user
        self.db = db

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate that the setting is able to be updated"""


class EmailSetting(ValidationSetting):
    def __init__(
        self,
        db: Session,
        user: AuthedUser,
        verification_url: str,
    ):
        self.verification_url = verification_url
        super().__init__(db, user)

    def update(self, new_email: str):
        """
        Update the user's email. This will send the user a verification email.

        This function assumes the email itself is valid,
        but it will call the `validate` function.
        """

        self.validate(new_email)

        self.user.is_email_verified = False
        self.user.email = new_email

        email_verification.send_verification_email(
            self.user.email,
            self.verification_url,
        )

    def validate(self, new_email: str):
        """
        Validate that the email can be updated:
            - check if the email is taken
        """

        user_crud.original_email_or_raise(self.db, new_email)


class UsernameSetting(ValidationSetting):
    def __init__(
        self, db: Session, user: AuthedUser, edit_timedelta: timedelta
    ):
        self.edit_timedelta = edit_timedelta
        super().__init__(db, user)

    def update(self, new_username: str):
        """
        Update the user's username.

        This function assumes the username itself is valid,
        but it will call the `validate` function
        """

        self.validate(new_username)

        self.user.username_last_changed = datetime.utcnow()
        self.user.username = new_username

    def validate(self, new_username: str):
        """
        Validate that the username can be updated:
            - check if the username is taken
            - check if the username was changed too recently
        """

        user_crud.original_username_or_raise(self.db, new_username)

        now = datetime.utcnow()
        if (
            self.user.username_last_changed
            and self.user.username_last_changed + self.edit_timedelta > now
        ):
            raise HTTPException(
                status_code=HTTPStatus.TOO_MANY_REQUESTS,
                detail="Username changed too recently",
            )


def update_setting_single(
    db: Session, setting: Setting, new_value: Any
) -> AuthedUser:
    """
    Update a setting and commit to the database.

    :param db: the database session to use
    :param setting: the setting object
    :param new_value: which value to pass to the update function
    :return: the updated user
    """

    setting.update(new_value)
    db.commit()
    return setting.user


def update_settings_many(
    db: Session, target: Base, to_edit: dict[str, Any]
) -> Base:
    for setting, value in to_edit.items():
        setattr(target, setting, value)
    db.commit()
    return target
