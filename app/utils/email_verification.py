from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer

from app.services.email_service import EmailService
from app.models.user import User

from ..schemes.config import get_settings

serializer = URLSafeTimedSerializer(get_settings().secret_key)


def create_message(token: str | bytes) -> MIMEMultipart:
    """Render the email verification template into a mime multipart message"""

    message = MIMEMultipart("alternative")
    message["Subject"] = "Chess 2 Email Verification"

    message.attach(
        MIMEText(
            Jinja2Templates(directory="templates")
            .get_template(
                "email_verification.html",
            )
            .render(
                verification_url=get_settings().frontend_urls[0],
                verification_token=token,
            ),
            "html",
        )
    )
    return message


def create_or_get_verification_token(user: User) -> str | bytes:
    """
    Create or get an email verification token.
    This function checks if there is an outgoing verification request, and if there isn't it creates one.
    """

    token = serializer.dumps(user.email, "email-confirm-key")
    return token


def send_verification_email(user: User) -> None:
    """Create a verification request and send an email to the user."""

    token = create_or_get_verification_token(user)
    message = create_message(token)
    EmailService.send(message, user.email)
