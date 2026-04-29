import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def build_service():
    creds = None
    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _decode_body(payload: dict) -> str:
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""


def _get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


class GmailClient:
    def __init__(self):
        self._service = build_service()

    def fetch_unread(self) -> list[dict]:
        result = self._service.users().messages().list(
            userId="me", labelIds=["INBOX", "UNREAD"]
        ).execute()
        messages = result.get("messages", [])
        emails = []
        for m in messages:
            msg = self._service.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            headers = msg["payload"]["headers"]
            emails.append({
                "id": msg["id"],
                "sender": _get_header(headers, "From"),
                "subject": _get_header(headers, "Subject"),
                "message_id": _get_header(headers, "Message-ID"),
                "body": _decode_body(msg["payload"]),
            })
        return emails

    def send_email(self, to: str, subject: str, body: str, reply_to_id: str = "") -> None:
        mime = MIMEText(body, "plain", "utf-8")
        mime["To"] = to
        mime["Subject"] = subject
        if reply_to_id:
            mime["In-Reply-To"] = reply_to_id
            mime["References"] = reply_to_id
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        self._service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

    def mark_as_read(self, msg_id: str) -> None:
        self._service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
