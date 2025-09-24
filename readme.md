# AI Meeting Scheduler

This is a Flask web application that functions as an intelligent chat agent for scheduling meetings. It uses Google's Gemini model to understand natural language requests and the Google Calendar API to schedule events directly in a user's calendar.



## Features

-   **Natural Language Processing**: Schedule meetings by typing requests like "Book a sync with jane@example.com tomorrow at 3 PM".
-   **Google Sign-In**: Securely authenticates users with their Google accounts.
-   **Google Calendar Integration**: Automatically creates events and sends invitations.
-   **Google Meet Links**: Automatically generates a Google Meet link for every scheduled event.
-   **Confirmation Modal**: Shows a summary of the meeting for user approval before finalizing.

## Prerequisites

Before you begin, ensure you have the following:
-   Python 3.8+
-   A MongoDB account and your connection string.
-   A Google Cloud Platform project.

## Setup Instructions

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Shakti0071/Training/tree/master
    cd <training>
    ```

2.  **Install Dependencies**: Create a file named `requirements.txt` with the content below and run `pip install -r requirements.txt`.
    ```text
    # requirements.txt
    Flask
    pymongo[srv]
    google-api-python-client
    google-auth-oauthlib
    python-dateutil
    google-generativeai
    ```

3.  **Set Up Google Cloud**:
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Enable the **Google Calendar API** for your project.
    -   Create an **OAuth 2.0 Client ID**, select "Web application," and add `http://localhost:5000/oauth2callback` as an "Authorized redirect URI."
    -   Download the credentials JSON file and rename it to `credentials.json` in your project's root directory.

4.  **Configure Application**:
    -   In `d2app.py`, update the `MongoClient()` with your MongoDB connection string.
    -   In `d2app.py`, update the `GENAI_API_KEY` with your Google Gemini API key.

5.  **Run the Application**:
    ```bash
    python d2app.py
    ```
    Open your browser and navigate to `http://localhost:5000`.

## Usage

Once logged in, simply type a message into the chat box to schedule a meeting. The AI will parse your request and ask for confirmation before creating the calendar event.