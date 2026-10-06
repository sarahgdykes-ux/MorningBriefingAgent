import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.litellm import LiteLLMModel
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from slack_sdk import WebClient

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

SCOPES = ["gmail.readonly", "calendar.readonly"]


def get_google_credentials():
    """Get or refresh Google API credentials for Gmail and Calendar."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "credentials.json not found. Please download it from Google Cloud Console "
                    "and place it in the project directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


@tool
def check_gmail(hours_back: int = 12) -> str:
    """Fetch UNREAD emails from the last N hours via Gmail API.
    Returns sender, subject, date, and a snippet truncated to 200 chars.
    """
    try:
        creds = get_google_credentials()
        service = build("gmail", "v1", credentials=creds)
        
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        cutoff_str = cutoff.strftime("%Y/%m/%d")
        
        results = service.users().messages().list(
            userId="me",
            q=f"is:unread after:{cutoff_str}"
        ).execute()
        
        messages = results.get("messages", [])
        if not messages:
            return f"No unread emails found in the last {hours_back} hours."
        
        email_list = []
        for msg in messages[:20]:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            
            headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
            snippet = msg_data.get("snippet", "")[:200]
            
            email_list.append(
                f"From: {headers.get('From', 'Unknown')}\n"
                f"Subject: {headers.get('Subject', 'No subject')}\n"
                f"Date: {headers.get('Date', 'Unknown')}\n"
                f"Snippet: {snippet}\n"
            )
        
        return "\n---\n".join(email_list)
    except Exception as e:
        return f"Error fetching Gmail: {str(e)}"


@tool
def check_calendar(hours_ahead: int = 24) -> str:
    """Fetch upcoming events from the primary calendar for the next N hours.
    Returns title, start, end, location, and attendees.
    """
    try:
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)
        
        now = datetime.utcnow().isoformat() + "Z"
        time_max = (datetime.utcnow() + timedelta(hours=hours_ahead)).isoformat() + "Z"
        
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        events = events_result.get("items", [])
        if not events:
            return f"No upcoming events in the next {hours_ahead} hours."
        
        event_list = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            location = event.get("location", "No location")
            attendees = event.get("attendees", [])
            attendee_names = [a.get("displayName", a.get("email", "Unknown")) for a in attendees]
            
            event_list.append(
                f"Title: {event.get('summary', 'No title')}\n"
                f"Start: {start}\n"
                f"End: {end}\n"
                f"Location: {location}\n"
                f"Attendees: {', '.join(attendee_names) if attendee_names else 'None'}\n"
            )
        
        return "\n---\n".join(event_list)
    except Exception as e:
        return f"Error fetching Calendar: {str(e)}"


@tool
def check_slack(hours_back: int = 12, max_channels: int = 5) -> str:
    """Fetch recent messages from Slack channels.
    Lists channels I'm a member of, picks the most recently active ones,
    and returns channel name plus up to 5 recent messages per channel.
    """
    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        
        channels_result = client.conversations_list(types=["public_channel", "private_channel"])
        channels = [c for c in channels_result["channels"] if c.get("is_member")]
        
        if not channels:
            return "No Slack channels found."
        
        channel_info = []
        for channel in channels:
            try:
                history = client.conversations_history(
                    channel=channel["id"],
                    limit=1,
                    oldest=cutoff.timestamp()
                )
                if history["messages"]:
                    channel_info.append({
                        "name": channel["name"],
                        "id": channel["id"],
                        "timestamp": float(history["messages"][0].get("ts", 0))
                    })
            except Exception:
                continue
        
        channel_info.sort(key=lambda x: x["timestamp"], reverse=True)
        top_channels = channel_info[:max_channels]
        
        if not top_channels:
            return f"No recent Slack activity in the last {hours_back} hours."
        
        all_messages = []
        for ch in top_channels:
            try:
                history = client.conversations_history(
                    channel=ch["id"],
                    limit=5,
                    oldest=cutoff.timestamp()
                )
                messages = history.get("messages", [])
                if messages:
                    msg_texts = [f"{m.get('user', 'Unknown')}: {m.get('text', '')}" for m in messages]
                    all_messages.append(
                        f"Channel: #{ch['name']}\n" +
                        "\n".join(msg_texts)
                    )
            except Exception as e:
                all_messages.append(f"Channel: #{ch['name']}\nError: {str(e)}")
        
        return "\n---\n".join(all_messages)
    except Exception as e:
        return f"Error fetching Slack: {str(e)}"


SYSTEM_PROMPT = """You are a morning briefing assistant. You must ALWAYS call all three tools in this order:
1. check_gmail
2. check_calendar
3. check_slack

After gathering information, synthesize a prioritized morning briefing with these exact section headings:

URGENT
UPCOMING EVENTS
SLACK HIGHLIGHTS
OTHER EMAILS
SUGGESTED ACTIONS

Keep it concise and prioritized. If a source returned nothing or errored, explicitly state that. Focus on what matters most for the day ahead."""


def run():
    """Create the agent and run the morning briefing."""
    model = LiteLLMModel(
        client_args={
            "api_key": OPENROUTER_API_KEY,
            "api_base": "https://openrouter.ai/api/v1"
        },
        model_id="openrouter/openai/gpt-3.5-turbo",
        params={"max_tokens": 4096}
    )
    
    agent = Agent(
        model=model,
        tools=[check_gmail, check_calendar, check_slack],
        system_prompt=SYSTEM_PROMPT
    )
    
    result = agent("What did I miss? Give me my morning briefing.")
    print(result)


if __name__ == "__main__":
    run()
