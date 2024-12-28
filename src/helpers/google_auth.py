from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def resolve_credentials():
    """
    Resolves and returns valid Google API credentials.
    """
    # Determine the directory where this script resides
    script_dir = Path(__file__).parent.resolve()

    creds = None

    # Define paths for token.json and credentials.json
    token_path = script_dir / "token.json"
    credentials_path = script_dir / "credentials.json"

    # Load existing credentials from token.json if it exists
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            print(f"Loaded credentials from {token_path}")
        except Exception as e:
            print(f"Error loading credentials from {token_path}: {e}")

    # If credentials are invalid or don't exist, attempt to refresh or initiate OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Credentials refreshed successfully.")
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None

        if not creds or not creds.valid:
            if not credentials_path.exists():
                error_msg = f"Credentials file not found at {credentials_path}. Please ensure 'credentials.json' is in the correct directory."
                print(error_msg)
                raise FileNotFoundError(error_msg)
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
                print("Obtained new credentials via OAuth2 flow.")
            except Exception as e:
                print(f"Failed to obtain credentials: {e}")
                raise

    # Save the credentials for future use
    try:
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
            print(f"Saved credentials to {token_path}")
    except Exception as e:
        print(f"Failed to save credentials to {token_path}: {e}")

    return creds
