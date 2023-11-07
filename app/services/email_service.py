from email.mime.multipart import MIMEMultipart
import base64
import os

from google.auth.external_account_authorized_user import (
    Credentials as ExternalAccountCredentials,
)
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials as OAuth2Credentials

Credentials = OAuth2Credentials | ExternalAccountCredentials


def get_creds(scopes: list[str], credentials_file: str, token_file: str) -> Credentials:
    """
    Retrieves or revalidates credentials.

    :param scopes: the list of authorization scopes to request
    :param credentials_file: the file path to the credentials created by the google cloud console
    :param token_file: the path to save the received gmail tokens

    :return: the google api credentials object
    """

    creds: Credentials | None = None
    if os.path.exists(token_file):
        creds = OAuth2Credentials.from_authorized_user_file(token_file, scopes)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        creds = revalidate_creds(creds, scopes, credentials_file, token_file)

    return creds


def revalidate_creds(
    creds: Credentials | None,
    scopes: list[str],
    credentials_file: str,
    token_file: str,
) -> Credentials:
    """
    Revalidate expired or missing credentials by either refreshing them to creating new ones.

    :param creds: the existing credentials or none if there are no valid credentials
    :param scopes: the list of authorization scopes to request
    :param credentials_file: the file path to the credentials created by the google cloud console
    :param token_file: the path to save the received gmail tokens

    :return: the revalidated credentials
    """

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
        creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    with open(token_file, "w") as token:
        token.write(creds.to_json())

    return creds


def build_gmail_service(
    credentials_file: str,
    token_file: str,
    api_version: str,
    scopes: list[str],
) -> Resource:
    """
    Builds a gmail api service instance using the provided credentials and api info.

    :param credentials_file: the file path to the credentials created by the google cloud console
    :param token_file: the path to save the received gmail tokens
    :param api_version: the version of the google api to use
    :param scopes: the list of authorization scopes to request

    :return: the gmail api service instance
    """

    creds = get_creds(scopes, credentials_file, token_file)

    try:
        return build(
            "gmail",
            api_version,
            credentials=creds,
            static_discovery=False,
        )
    except:
        print(f"Failed to create gmail service instance for google api::{api_version}")
        raise


class EmailService:
    service = build_gmail_service(
        "google_tokens/auth_self_credentials.json",
        "google_tokens/gmail_api_tokens.json",
        "v1",
        ["https://mail.google.com/"],
    )

    @classmethod
    def send(cls, message: MIMEMultipart, recipient_email: str):
        """Send a mime multipart message from the authorized email."""

        message["To"] = recipient_email
        cls.service.users().messages().send(  # type: ignore
            userId="me",
            body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()},
        ).execute()
