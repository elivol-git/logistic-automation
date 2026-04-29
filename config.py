import os
from dotenv import load_dotenv

load_dotenv()

KEYWORDS = [
    "פריקת מכולות",
    "פריקת המכולה",
    "unload container",
    "unload containers",
]

NOTIFICATION_EMAIL = os.environ["NOTIFICATION_EMAIL"]
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
LOG_FILE = os.getenv("LOG_FILE", "automation.log")
