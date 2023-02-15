import os

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import base64

def create_service(client_secret_file, api_name, api_version, *scopes, prefix=""):
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    
    creds = None
    working_dir = os.getcwd()
    token_dir = "google_tokens"
    token_file = f"token_{API_SERVICE_NAME}_{API_VERSION}{prefix}.json"

    if not os.path.exists(os.path.join(working_dir, token_dir)): os.mkdir(os.path.join(working_dir, token_dir))

    if os.path.exists(os.path.join(working_dir, token_dir, token_file)): creds = Credentials.from_authorized_user_file(os.path.join(working_dir, token_dir, token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(os.path.join(working_dir, token_dir, token_file), "w") as token:
            token.write(creds.to_json())

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=creds, static_discovery=False)
        print(API_SERVICE_NAME, API_VERSION, "service created successfully")
        return service
    except Exception as e:
        print(e)
        print(f"Failed to create service instance for {API_SERVICE_NAME}")
        os.remove(os.path.join(working_dir, token_dir, token_file))
        return

service = create_service("google_tokens/email_auth.json", "gmail", "v1", ["https://mail.google.com/"])

sender = "willigooden.uk@gmail.com"
receiver = "willigooden.uk@gmail.com"

message = MIMEMultipart("alternative")
message["To"] = receiver
message["Subject"] = "test"

message.attach(MIMEText("""<html>
    <head>
        <style>
            .container {
                font-family:system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                text-align: center;
            }

            a {
                background-color: #4CAF50;
                border: none;
                color: white !important;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                border-radius: 8px;
                font-weight: bold;
                opacity: 90%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div style="background-color: rgb(247, 247, 248);">
                <h1 style="font-weight: bolder; padding-top: 100px; padding-bottom: 30px; font-size: 60px; margin: 0;">Welcome to Chess 2!</h1>
            </div>
            <div style="background-color: rgb(122, 150, 224);">
                <h3 style="margin: 0; padding-top: 50px; padding-bottom: 30px;">click the button bellow to verify your email!</h3>
                <a style="margin: 0;" href="https://youtube.com/">VERIFY</a>
                <div style="padding-top: 30px;"></div>
            </div>
        </div>
    </body>
</html>""", "html"))

service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()