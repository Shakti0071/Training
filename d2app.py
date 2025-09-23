import os
import json
from datetime import datetime, timedelta
import dateparser

from flask import Flask, request, redirect, url_for, session, render_template, jsonify
from pymongo import MongoClient
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import requests
from send_meeting import create_google_meeting
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Google OAuth Config ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_AUTH_URI = os.getenv("GOOGLE_AUTH_URI")
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI")
GOOGLE_CERT_URL = os.getenv("GOOGLE_CERT_URL")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": GOOGLE_AUTH_URI,
        "token_uri": GOOGLE_TOKEN_URI,
        "auth_provider_x509_cert_url": GOOGLE_CERT_URL,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI]
    }
}

# --- Flask App ---
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]

# --- MongoDB Connection ---
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["flaskdb"]
users_collection = db["users"]

# --- Fireworks AI Config ---
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_MODEL = os.getenv("FIREWORKS_MODEL")

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

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        return "⚠️ No valid response from Fireworks."
    except Exception as e:
        return f"🔥 Fireworks API error: {str(e)}"

# --- Helper: Normalize relative dates to absolute ---
def normalize_time(time_str):
    if not time_str:
        return None
    parsed = dateparser.parse(
        time_str,
        settings={
            "TIMEZONE": "Asia/Kolkata",
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now(),
        },
    )
    if not parsed:
        return None
    return parsed.strftime("%Y-%m-%d %H:%M")

# --- Helper: Convert datetime object to RFC3339 for Google Calendar ---
def to_rfc3339(dt_object):
    if not dt_object:
        raise ValueError("Cannot convert a null datetime object.")
    return dt_object.isoformat()

def parse_meeting_time(time_str, relative_base=None):
    if not time_str:
        return None
    base = relative_base or datetime.now()
    settings = {
        "TIMEZONE": "Asia/Kolkata",
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": base,
    }
    return dateparser.parse(time_str, settings=settings)

# --- Routes ---
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
            if "google_credentials" not in session:
                return redirect(url_for("authorize"))
            return redirect(url_for("chat"))
        else:
            message = "Invalid username or password!"
    return render_template("login.html", message=message)

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect(url_for("login"))
    if "google_credentials" not in session:
        return redirect(url_for("authorize"))
    return render_template("chat.html", username=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("google_credentials", None)
    return redirect(url_for("login"))

# --- Google OAuth Routes ---
@app.route("/authorize")
def authorize():
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=url_for("oauth2callback", _external=True),
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session["state"]
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG, scopes=SCOPES, state=state,
        redirect_uri=url_for("oauth2callback", _external=True),
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session["google_credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    return redirect(url_for("chat"))

# --- Chat Processing ---
@app.route("/process_chat_message", methods=["POST"])
def process_chat_message():
    user_message = request.json.get("message")

    prompt = f"""
        Analyze the user's request: "{user_message}"

        Extract title, start_time, end_time, and attendees.
        Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}.
        If no end time, default = 1 hour after start.

        Return ONLY JSON:
        {{
            "message": "confirmation",
            "meeting_proposal": {{
                "title": "string",
                "start_time": "string",
                "end_time": "string",
                "attendees": ["email1@example.com"]
            }}
        }}
    """

    bot_reply = call_fireworks_api(prompt)

    try:
        json_str = bot_reply[bot_reply.find("{"): bot_reply.rfind("}") + 1]
        data = json.loads(json_str)
    except Exception:
        return jsonify({"type": "chat", "reply": bot_reply})

    meeting_proposal = data.get("meeting_proposal")
    if not meeting_proposal or not meeting_proposal.get("start_time"):
        return jsonify({"type": "chat", "reply": data.get("message", bot_reply)})

    start_dt = parse_meeting_time(meeting_proposal.get("start_time"))
    end_dt = parse_meeting_time(meeting_proposal.get("end_time"))

    if not start_dt:
        return jsonify({"type": "chat", "reply": "❌ Couldn't understand meeting time."})

    if not end_dt or end_dt <= start_dt:
        end_dt = start_dt + timedelta(hours=1)

    attendees = meeting_proposal.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in attendees.split(",") if a.strip()]

    return jsonify({
        "type": "meeting_proposal",
        "message": data.get("message", "I can schedule this for you. Does this look right?"),
        "details": {
            "title": meeting_proposal.get("title", "Scheduled Meeting"),
            "start_time_display": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_time_display": end_dt.strftime("%Y-%m-%d %H:%M"),
            "attendees": attendees
        }
    })

# --- Schedule Meeting ---
@app.route("/schedule_meeting", methods=["POST"])
def schedule_meeting():
    if "google_credentials" not in session:
        return jsonify({"success": False, "message": "Authentication required."}), 401

    creds = Credentials.from_authorized_user_info(session["google_credentials"], SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        session["google_credentials"]["token"] = creds.token

    try:
        meeting_details = request.json
        if not meeting_details:
            return jsonify({"success": False, "message": "❌ No meeting details received."})

        title = meeting_details.get("title", "Scheduled Meeting")
        start_dt = parse_meeting_time(meeting_details.get("start_time"))
        end_dt = parse_meeting_time(meeting_details.get("end_time"))

        if not start_dt or not end_dt:
            return jsonify({"success": False, "message": "❌ Invalid start or end time."})

        start_rfc = to_rfc3339(start_dt)
        end_rfc = to_rfc3339(end_dt)

        service = build("calendar", "v3", credentials=creds)
        event_body = {
            "summary": title,
            "start": {"dateTime": start_rfc, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_rfc, "timeZone": "Asia/Kolkata"},
            "attendees": [{"email": email} for email in meeting_details.get("attendees", []) if email],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meeting-{datetime.now().timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }

        created_event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all"
        ).execute()

        return jsonify({
            "success": True,
            "message": "✅ Meeting scheduled!",
            "meet_link": created_event.get("hangoutLink"),
            "event_link": created_event.get("htmlLink"),
        })

    except Exception as e:
        import traceback
        print("🔥 ERROR TRACEBACK:", traceback.format_exc())
        return jsonify({"success": False, "message": str(e)})

# --- Run App ---
if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
    app.run(debug=True, port=5000)
