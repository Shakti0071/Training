import os
import json
from datetime import datetime
import dateparser

from flask import Flask, request, redirect, url_for, session, render_template, jsonify
from pymongo import MongoClient
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import requests

# --- Flask App ---
app = Flask(__name__)
app.secret_key = "4f3a6f9c9e4e2f3e9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# --- MongoDB Connection ---
client = MongoClient(
    "mongodb+srv://shakti4052_db_user:shakti1707@cluster0.dmyk79s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["flaskdb"]
users_collection = db["users"]

# --- Fireworks AI Config ---
FIREWORKS_API_KEY = "fw_3ZjYrkod6BN4JPDLM7BLLh5b"
FIREWORKS_MODEL = "accounts/fireworks/models/kimi-k2-instruct-0905"

def call_fireworks_api(user_message):
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": FIREWORKS_MODEL,
        "max_tokens": 1024,
        "temperature": 0.6,
        "messages": [
            {"role": "system", "content": "You are a helpful chatbot."},
            {"role": "user", "content": user_message}
        ]
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREWORKS_API_KEY}"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        data = response.json()
        print("=== Fireworks Raw Response ===")
        print(data)

        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return choice['message']['content']
            elif 'text' in choice:
                return choice['text']
        return "⚠️ No valid response from Fireworks."
    except Exception as e:
        return f"🔥 Fireworks API error: {str(e)}"

# --- Google Calendar Config ---
CLIENT_SECRETS_FILE = 'credentials.json'

# --- Helper: Normalize relative dates to absolute ---
def normalize_time(time_str):
    if not time_str:
        return None

    parsed = dateparser.parse(
        time_str,
        settings={
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': False,
            'PREFER_DATES_FROM': 'future',   # ensures "tomorrow" means future
            'RELATIVE_BASE': datetime.now(), # base reference is now
        }
    )
    if not parsed:
        return None
    return parsed.strftime("%Y-%m-%d %H:%M")


# --- Helper: Convert to RFC3339 for Google Calendar ---
def to_rfc3339(dt_str):
    parsed = dateparser.parse(dt_str, settings={'TIMEZONE': 'Asia/Kolkata', 'RETURN_AS_TIMEZONE_AWARE': True})
    if not parsed:
        raise ValueError(f"Could not parse datetime: {dt_str}")
    return parsed.isoformat()

# --- Standard Routes ---
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not username or not password or not confirm_password:
            message = "Please fill all fields."
        elif password != confirm_password:
            message = "Passwords do not match!"
        elif users_collection.find_one({"username": username}):
            message = "Username already exists!"
        else:
            users_collection.insert_one({"username": username, "password": password})
            return redirect(url_for("login"))
    return render_template("signup.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            session["username"] = username
            if 'google_credentials' not in session:
                return redirect(url_for('authorize'))
            return redirect(url_for("chat"))
        else:
            message = "Invalid username or password!"
    return render_template("login.html", message=message)

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    if 'google_credentials' not in session:
        return redirect(url_for('authorize'))
    return render_template("chat.html", username=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("google_credentials", None)
    return redirect(url_for("login"))

# --- Google OAuth Routes ---
@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['google_credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return redirect(url_for('chat'))

# --- Chat Processing Route ---
@app.route('/process_chat_message', methods=['POST'])
def process_chat_message():
    user_message = request.json.get('message')

    prompt = f"""
    User message: "{user_message}"

    You are a chatbot that schedules meetings.
    - Extract meeting details if scheduling is requested.
    - Support relative dates like "today", "tonight", "tomorrow", "next Monday".
    - Always return absolute dates in "YYYY-MM-DD HH:MM" format.
    - Do NOT hardcode past years; dates should be relative to today.

    Return JSON in this format:
    {{
        "message": "string (chatbot reply in natural language)",
        "meeting_proposal": {{
            "title": "string",
            "start_time": "YYYY-MM-DD HH:MM",
            "end_time": "YYYY-MM-DD HH:MM",
            "attendees": ["email1", "email2"]
        }} OR null
    }}
    """

    bot_reply = call_fireworks_api(prompt)

    try:
        data = json.loads(bot_reply)
    except Exception:
        try:
            json_str = bot_reply[bot_reply.find("{"): bot_reply.rfind("}")+1]
            data = json.loads(json_str)
        except Exception:
            return jsonify({"type": "chat", "reply": bot_reply})

    meeting_proposal = data.get("meeting_proposal")
    if not meeting_proposal:
        return jsonify({"type": "chat", "reply": data.get("message", bot_reply)})

    # --- Normalize attendees ---
    attendees = meeting_proposal.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",")]
    meeting_proposal["attendees"] = attendees

    # --- Normalize times ---
    now = datetime.now()

    def smart_normalize(time_str, user_message=None, default_duration_hours=1):
        """
        Parse Fireworks date robustly. Use relative phrases from user message if parsed date is in the past.
        Also, ensure end_time is after start_time by adding default_duration_hours if needed.
        """
        if not time_str:
            return None

        import re
        now = datetime.now()

        # Try parsing the Fireworks time
        parsed = dateparser.parse(
            time_str,
            settings={
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': False,
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': now
            }
        )

        # If parsing failed or date is in past, fallback to relative phrases from user message
        if not parsed or parsed < now:
            text_to_parse = user_message if user_message else time_str
            phrases = ["today", "tomorrow", "tonight", "next monday", "next tuesday",
                    "next wednesday", "next thursday", "next friday", "next saturday", "next sunday"]
            for phrase in phrases:
                if phrase in text_to_parse.lower():
                    parsed = dateparser.parse(
                        phrase,
                        settings={
                            'TIMEZONE': 'Asia/Kolkata',
                            'RETURN_AS_TIMEZONE_AWARE': False,
                            'PREFER_DATES_FROM': 'future',
                            'RELATIVE_BASE': now
                        }
                    )
                    break

        # Extract hour and minute from Fireworks string if present
        hour_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM|am|pm)?', time_str)
        if hour_match and parsed:
            hour = int(hour_match.group(1))
            minute = int(hour_match.group(2) or 0)
            ampm = hour_match.group(3)
            if ampm and ampm.lower() == "pm" and hour < 12:
                hour += 12
            if ampm and ampm.lower() == "am" and hour == 12:
                hour = 0
            parsed = parsed.replace(hour=hour, minute=minute)
        else:
            # Default times
            if parsed and 'tonight' in (user_message or '').lower():
                parsed = parsed.replace(hour=20, minute=0)
            elif parsed:
                parsed = parsed.replace(hour=16, minute=0)  # default 4 PM if nothing specified

        return parsed.strftime("%Y-%m-%d %H:%M") if parsed else None


    # --- Adjust end time if same as start ---
    def ensure_end_time(start_str, end_str, default_duration_minutes=60):
        from datetime import datetime, timedelta
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        if not end_str:
            end_dt = start_dt + timedelta(minutes=default_duration_minutes)
        else:
            end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M")
            if end_dt <= start_dt:
                end_dt = start_dt + timedelta(minutes=default_duration_minutes)
        return end_dt.strftime("%Y-%m-%d %H:%M")



    start_time = smart_normalize(meeting_proposal.get("start_time"), user_message)
    end_time = smart_normalize(meeting_proposal.get("end_time"), user_message)
    end_time = ensure_end_time(start_time, end_time, default_duration_minutes=60)


    meeting_proposal["start_time"] = start_time
    meeting_proposal["end_time"] = end_time

    return jsonify({
        "type": "meeting_proposal",
        "message": data.get("message", "I found a meeting slot."),
        "details": {
            "title": meeting_proposal.get("title", "Scheduled Meeting"),
            "start_time_display": start_time,
            "end_time_display": end_time,
            "attendees": attendees
        }
    })


# --- Schedule Meeting Route ---
@app.route('/schedule_meeting', methods=['POST'])
def schedule_meeting():
    if 'google_credentials' not in session:
        return jsonify({'error': 'Authentication required.'}), 401

    creds = Credentials.from_authorized_user_info(session['google_credentials'], SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        session['google_credentials']['token'] = creds.token

    try:
        meeting_details = request.json
        if not meeting_details:
            return jsonify({"success": False, "message": "❌ No meeting details received."})

        title = meeting_details.get('title', 'Scheduled Meeting')
        start_time = normalize_time(meeting_details.get("start_time"))
        end_time = normalize_time(meeting_details.get("end_time"))
        attendees = meeting_details.get('attendees', [])

        if not start_time or not end_time:
            return jsonify({"success": False, "message": "❌ Missing start or end time."})

        service = build("calendar", "v3", credentials=creds)

        event_body = {
            'summary': title,
            'start': {'dateTime': to_rfc3339(start_time), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': to_rfc3339(end_time), 'timeZone': 'Asia/Kolkata'},
            'attendees': [{'email': email} for email in attendees if email],
            'conferenceData': {
                'createRequest': {
                    'requestId': f'meeting-{datetime.now().timestamp()}',
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        # --- Send invitations immediately ---
        created_event = service.events().insert(
            calendarId='primary',
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates='all'  # Sends invitations to all attendees
        ).execute()

        # --- Fetch attendee response statuses ---
        attendee_statuses = {}
        for attendee in created_event.get('attendees', []):
            email = attendee.get('email')
            status = attendee.get('responseStatus', 'needsAction')  # 'accepted', 'declined', 'needsAction'
            attendee_statuses[email] = status

        return jsonify({
            "success": True,
            "meet_link": created_event.get('hangoutLink'),
            "event_link": created_event.get('htmlLink'),
            "start_time": start_time,
            "end_time": end_time,
            "attendee_statuses": attendee_statuses
        })

    except Exception as e:
        import traceback
        print("🔥 ERROR TRACEBACK:", traceback.format_exc())
        return jsonify({"success": False, "message": str(e)})

# --- Run Flask App ---
if __name__ == "__main__":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run(debug=True, port=5000)
