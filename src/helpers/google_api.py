# src/helpers/google_api.py
import logging
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build
from google.oauth2 import service_account

# Set up logging
logging.basicConfig(filename="app.log", level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Connection:
    def __init__(self):
        self.user = "luis1abreu11@gmail.com"  # Calendar ID / Task List ID
        self.scopes = ["https://www.googleapis.com/auth/calendar.readonly", "https://www.googleapis.com/auth/tasks.readonly", 
                       "https://www.googleapis.com/auth/tasks", "https://www.googleapis.com/auth/calendar"]
        self._credentials = service_account.Credentials.from_service_account_file(
                str(Path(__file__).parent / 'red.json'), scopes=self.scopes
            )
        self.calendar_service = self._calendar_service()
        self.task_service = self._task_service()
        
        # Path to your Service Account JSON key file
        credentials_path = Path(__file__).parent / 'red.json'
        
        if not credentials_path.exists():
            raise FileNotFoundError(f"Service account file not found at {credentials_path}")

        
    def _task_service(self):
        task_service = build("tasks", "v1", credentials=self._credentials)
        return task_service

    def _calendar_service(self):
        service = build("calendar", "v3", credentials=self._credentials)
        return service

    def get_cal(self):
        """
        Fetches today's events from the Google Calendar.
        Returns:
            List of event dictionaries.
        """
        try:
            # Current UTC time
            now = datetime.now(timezone.utc) 
            
            # Start of today in UTC
            start_of_today = now.replace(hour=0, minute=0, second=10, microsecond=10).isoformat()
            # End of today in UTC
            end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
            
            # Fetch events from the calendar
            event_results = self.calendar_service.events().list(
                calendarId=self.user,
                timeMin=start_of_today,
                timeMax=end_of_today,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = event_results.get("items", [])
            #logging.info(f'Events: {events}')
            if not events:
                logger.info("No upcoming events found for today.")
                return []
            
            logger.info(f"Fetched {len(events)} events from the calendar.")
            return events  # Return the list of event dicts
        
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            return []


    def get_tasks(self):
        """
        Fetches today's tasks from Google Tasks.
        Returns:
            List of task dictionaries.
        """
        try:
            # Fetch tasks from the task list
            task_results = self.task_service.tasks().list(tasklist="@default", maxResults=10).execute()

            tasks = task_results.get("items", [])
            logger.info(task_results)
            if not tasks:
                logger.info("No tasks found for today.")
                return []
            
            logger.info(f"Fetched {len(tasks)} tasks from Google Tasks.")
            return tasks  # Return the list of task dicts
        
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

