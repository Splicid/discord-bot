from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import os
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def resolve_credentials(credentials):
  
    script_dir = Path(__file__).parent.resolve()
    creds = None

    token_path = script_dir / "token.json"
    if token_path.exists:
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Error loading credentials from {credentials}: {e}")

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None

    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        except Exception as e:
            print(f"Failed to obtain credentials: {e}")
            raise
    # Save the credentials for the next run
    try:
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    except Exception as e:
        print(f"Failed to save credentials to {credentials}: {e}")

    return creds
        


    