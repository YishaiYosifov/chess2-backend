from datetime import datetime
from http import HTTPStatus
from abc import abstractmethod, ABC

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.utils import email_verification
from app.crud import user_crud

from ..models.user import User


class Setting(ABC):
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    @abstractmethod
    def update(self, value: str):
        pass


class ValidationSetting(Setting, ABC):
    @abstractmethod
    def validate(self, value):
        """Validate that the setting is able to be updated"""


class PasswordSetting(Setting):
    def update(self, value: str):
        # TODO
        pass


class EmailSetting(ValidationSetting):
    def __init__(self, user: User):
        self.user = user

    def update(self, new_email: str):
        """
        Update the user's email. This will send the user a verification email.

        This function assumes the email itself is valid,
        but it will call the `validate` function.
        """

        self.user.is_email_verified = False
        self.user.email_last_changed = datetime.now()
        self.user.email = new_email

        # TODO: this method shouldn't be in the user class. it should probably be in some email service
        email_verification.send_verification_email(self.user)

    def validate(self, new_email: str):
        """
        Validate that the email can be updated:
            - check if the email is taken
            - check if the email was changed too recently
        """

        if user_crud.fetch_by(email=new_email):
            fail_abort({"email": "Email Taken"}, HTTPStatus.CONFLICT)

        now = datetime.utcnow()
        email_edit_every = current_app.config.get("EMAIL_EDIT_EVERY", timedelta(days=1))
        if (
            self.user.email_last_changed
            and self.user.email_last_changed + email_edit_every > now
        ):
            fail_abort(
                {"email": "Email changed too recently"}, HTTPStatus.TOO_MANY_REQUESTS
            )


class UsernameSetting(ValidationSetting):
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

        if user_crud.fetch_by(self.db, User.username == new_username):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail={"username": "Username Taken"},
            )

        now = datetime.utcnow()
        username_edit_every = current_app.config.get(
            "USERNAME_EDIT_EVERY", timedelta(weeks=4)
        )
        if (
            self.user.username_last_changed
            and self.user.username_last_changed + username_edit_every > now
        ):
            fail_abort(
                {"username": "Username changed too recently"},
                HTTPStatus.TOO_MANY_REQUESTS,
            )
