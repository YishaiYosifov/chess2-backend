from datetime import timedelta, datetime
from typing import Any
from http import HTTPStatus
from abc import abstractmethod, ABC

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.utils import email_verification
from app.crud import user_crud

from ..models.user import User


class Setting(ABC):
    def __init__(self, user: User) -> None:
        self.user = user

    @abstractmethod
    def update(self, value: str) -> None:
        pass


class ValidationSetting(Setting, ABC):
    def __init__(self, user: User, db: Session) -> None:
        self.user = user
        self.db = db

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate that the setting is able to be updated"""


class EmailSetting(ValidationSetting):
    def __init__(
        self,
        user: User,
        db: Session,
        edit_timedelta: timedelta,
        verification_url: str,
    ):
        self.verification_url = verification_url
        self.edit_timedelta = edit_timedelta
        super().__init__(user, db)

    def update(self, new_email: str):
        """
        Update the user's email. This will send the user a verification email.

        This function assumes the email itself is valid,
        but it will call the `validate` function.
        """

        self.validate(new_email)

        self.user.is_email_verified = False
        self.user.email_last_changed = datetime.now()
        self.user.email = new_email

        email_verification.send_verification_email(
            self.user.email,
            self.verification_url,
        )

    def validate(self, new_email: str):
        """
        Validate that the email can be updated:
            - check if the email is taken
            - check if the email was changed too recently
        """

        user_crud.original_email_or_raise(self.db, new_email)

        now = datetime.utcnow()
        if (
            self.user.email_last_changed
            and self.user.email_last_changed + self.edit_timedelta > now
        ):
            raise HTTPException(
                status_code=HTTPStatus.TOO_MANY_REQUESTS,
                detail={"email": "Email changed too recently"},
            )


class UsernameSetting(ValidationSetting):
    def __init__(self, user: User, db: Session, edit_timedelta: timedelta):
        self.edit_timedelta = edit_timedelta
        super().__init__(user, db)

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
                detail={"username": "Username changed too recently"},
            )
