from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer

from app.services.email_service import EmailService

from ..schemas.config_schema import get_config

serializer = URLSafeTimedSerializer(get_config().secret_key)


def create_message(verification_url: str, token: str | bytes) -> MIMEMultipart:
    """
    Render the email verification template into a mime multipart message

    :param verification_url: the frontend url that the user will be directed to when clicking on the email
    :param token: the generated email verification token
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Chess 2 Email Verification"

    message.attach(
        MIMEText(
            Jinja2Templates(directory="templates")
            .get_template(
                "email_verification.html",
            )
            .render(
                verification_url=verification_url,
                verification_token=token,
            ),
            "html",
        )
    )
    return message


def create_or_get_verification_token(email: str) -> str | bytes:
    """
    Create or get an email verification token.
    This function checks if there is an outgoing verification request, and if there isn't it creates one.
    """

    token = serializer.dumps(email, "email-confirm-key")
    return token


def send_verification_email(email: str, verification_url: str) -> None:
    """
    Create a verification request and send an email to the user.

    :param email: the email to send the verification email to
    :param verification_url: the frontend url that the user will be directed to when clicking on the email
    """

    token = create_or_get_verification_token(email)
    message = create_message(verification_url, token)
    EmailService.send(message, email)
