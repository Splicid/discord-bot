# src/helpers/google_api.py
import logging
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2 import service_account

class Connection:
    def __init__(self):
        self.user = "luis1abreu11@gmail.com"  # Optional: Remove if not used elsewhere
        self.service = self._create_service()

    def _create_service(self):
        """
        Creates a Google Calendar service using Service Account credentials.
        """
        try:
            # Path to your Service Account JSON key file
            credentials_path = Path(__file__).parent / 'red.json'
            
            if not credentials_path.exists():
                raise FileNotFoundError(f"Service account file not found at {credentials_path}")
            
            # Define the scopes
            SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
            
            # Create credentials using the service account
            credentials = service_account.Credentials.from_service_account_file(
                str(credentials_path), scopes=SCOPES
            )
            
            service = build("calendar", "v3", credentials=credentials)
            logging.info("Google Calendar service initialized successfully with Service Account.")
            return service
        except Exception as e:
            logging.error(f"Failed to create Google Calendar service: {e}")
            raise

    def get_cal(self):
        try:
            # Current UTC time
            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()
            
            # Start of today in UTC
            start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

            # Fetch events from the calendar
            event_results = self.service.events().list(
                calendarId=self.user,
                timeMin=start_of_today,
                timeMax=now_iso,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = event_results.get("items", [])
            if not events:
                return "No upcoming events found for today."
            
            # Use list comprehension for efficiency and readability
            todays_events = [
                f"{event['start'].get('dateTime', event['start'].get('date'))} - {event.get('summary', 'No Title')}"
                for event in events
            ]
            
            return "\n".join(todays_events)
        
        except Exception as e:
            logging.error(f"Error fetching calendar events: {e}")
            return "Failed to retrieve calendar events."