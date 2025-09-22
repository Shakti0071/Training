# send_meeting.py
import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from datetime import datetime

# Path to token.json and credentials.json
TOKEN_PATH = 'token.json'  # generated after OAuth flow
CREDENTIALS_PATH = 'credentials.json'  # your Google API credentials

# send_meeting.py
from googleapiclient.discovery import build
from datetime import datetime

def create_google_meeting(credentials, title, start_time_iso, end_time_iso, attendees_emails):
    """
    Schedules a Google Meet using provided credentials and event details.

    Args:
        credentials: An authorized Google OAuth2 credentials object.
        title (str): Title of the meeting.
        start_time_iso (str): Start time in ISO format 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        end_time_iso (str): End time in ISO format 'YYYY-MM-DDTHH:MM:SS±HH:MM'.
        attendees_emails (list): List of email addresses to invite.
    
    Returns:
        dict: The created event details from the Google Calendar API.
    """
    try:
        service = build('calendar', 'v3', credentials=credentials)

        event = {
            'summary': title,
            'start': {
                'dateTime': start_time_iso,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_time_iso,
                'timeZone': 'Asia/Kolkata',
            },
            'attendees': [{'email': email} for email in attendees_emails if email],
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{datetime.now().timestamp()}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                }
            },
        }

        created_event = service.events().insert(
            calendarId='primary',
            body=event,
            conferenceDataVersion=1,
            sendUpdates='all'  # Sends invitation emails to attendees
        ).execute()

        print("✅ Meeting scheduled successfully via send_meeting.py!")
        return created_event

    except Exception as e:
        print(f"❌ Failed to create meeting using send_meeting.py: {e}")
        raise e

# Example usage (for testing)
if __name__ == "__main__":
    meeting = create_google_meeting(
        title="Demo Meeting",
        start_time="2025-09-18T15:00:00",
        end_time="2025-09-18T16:00:00",
        attendees_emails=["example1@gmail.com", "example2@gmail.com"]
    )
    print(meeting)

