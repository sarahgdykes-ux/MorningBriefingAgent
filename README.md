# Morning Briefing Agent

A Python agent that checks your Gmail, Google Calendar, and Slack, then synthesizes a prioritized morning briefing.

## Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or: source .venv/bin/activate  # On macOS/Linux
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your `ANTHROPIC_API_KEY` (preferred) or `OPENROUTER_API_KEY` from https://openrouter.ai/keys
   - Fill in your `SLACK_BOT_TOKEN` (user token with `xoxp-` prefix, scopes: `channels:read`, `channels:history`, `groups:read`, `groups:history`)

4. **Configure urgency and filtering (optional):**
   - Edit `agent.py` to customize `IMPORTANT_CONTACTS` list (emails/domains that are always urgent)
   - Edit `agent.py` to customize `MARKETING_DOMAINS` list (domains to filter out)
   - Urgent keywords are pre-configured: "action required", "urgent", "deadline"

5. **Set up Google credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Gmail API and Calendar API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials JSON file and rename it to `credentials.json`
   - Place `credentials.json` in the project directory

6. **First-run browser login:**
   - Run the agent once: `python agent.py`
   - A browser window will open for Google OAuth consent
   - After authorization, `token.json` will be saved for future runs

## Running

- **Test the model connection:**
  ```bash
  python test_model.py
  ```

- **Run the morning briefing:**
  ```bash
  python agent.py
  ```

## Testing Individual Tools

Test each tool in isolation with these one-liners:

```bash
python -c "from agent import check_gmail; print(check_gmail(hours_back=24))"
```

```bash
python -c "from agent import check_calendar; print(check_calendar(hours_ahead=24))"
```

```bash
python -c "from agent import check_slack; print(check_slack(hours_back=24))"
```

## Output Format

The agent produces a briefing with these sections:
- **URGENT** - Items requiring immediate attention (emails from important contacts or with urgent keywords)
- **UPCOMING EVENTS** - Calendar events for the day
- **SLACK HIGHLIGHTS** - Recent activity in top channels
- **OTHER EMAILS** - Less urgent unread emails (marketing emails are filtered out)
- **SUGGESTED ACTIONS** - Prioritized next steps

## Features

- **Smart Urgency Detection**: Emails from configured important contacts or with urgent keywords are automatically marked as urgent
- **Marketing Filter**: Emails from configured marketing domains are filtered out before reaching the AI
- **Multi-Source Integration**: Aggregates data from Gmail, Google Calendar, and Slack
- **Prioritized Briefing**: Synthesizes information into a concise, actionable morning briefing
