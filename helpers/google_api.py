from datetime import datetime, timezone
import os.path
from pathlib import Path


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from google_auth import resolve_credentials


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
credentials_path = Path(__file__).parent / 'credentials.json'

class Connection:
  def __init__(self):
    self.user = "luis1abreu11@gmail.com"
    self._sa = resolve_credentials(credentials_path)
    _scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
  
  @property
  def _calendar_conn(self):
    service = build("calendar", "v3", credentials=self._sa)
    return service
  
  def get_cal(self):
      try:
        # est time zone
        now = datetime.now(timezone.utc).isoformat()
        today = datetime.now(timezone.utc)

        start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_today = start_of_today.isoformat() 

        cal_connection = self._calendar_conn
        event_results = cal_connection.events().list(
          calendarId="primary",
          timeMin=start_of_today,
          timeMax=now,
          maxResults=10,
          singleEvents=True,
          orderBy="startTime",
        ).execute() 

        events = event_results.get("items", [])
        todays_events = []
        for event in events:
          start = event["start"].get("dateTime", event["start"].get("date"))
          todays_events.append(f"{start} - {event['summary']}")
        return todays_events
          
      except Exception as e:
        print(f"{e}")
    

if __name__ == "__main__":
  cal = Connection()
  print(cal.get_cal())