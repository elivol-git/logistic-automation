# Gmail Auto-Reply Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python service that polls Gmail every 5 minutes, detects container-unloading emails by keyword, generates AI replies via Claude, sends reply + notification, and marks email as read.

**Architecture:** Cron-driven polling loop in `main.py` orchestrates five focused modules: Gmail client, keyword/language detector, Claude client, config, and logger. No database — idempotency via Gmail's UNREAD label (processed emails are marked read).

**Tech Stack:** Python 3.10+, `google-api-python-client`, `google-auth-oauthlib`, `anthropic`, `python-dotenv`, `pytest`

---

## File Map

| Path | Role |
|------|------|
| `config.py` | All configurable values, loaded from `.env` |
| `logger.py` | File-based structured logger |
| `detector.py` | Keyword matching + Hebrew/English language detection |
| `gmail_client.py` | Gmail API wrapper: fetch unread, send email, mark read |
| `claude_client.py` | Claude API wrapper: generate subject + body |
| `main.py` | Orchestrator: poll → detect → reply → notify → mark read |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for secrets |
| `.gitignore` | Ignore `.env`, `token.json`, logs |
| `tests/test_detector.py` | Unit tests for detector |
| `tests/test_gmail_client.py` | Unit tests for gmail_client (mocked) |
| `tests/test_claude_client.py` | Unit tests for claude_client (mocked) |
| `tests/test_main.py` | Unit tests for main orchestrator (mocked) |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config.py`

- [ ] **Step 1: Create `requirements.txt`**

```
google-api-python-client==2.118.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
anthropic==0.49.0
python-dotenv==1.0.1
pytest==8.3.5
pytest-mock==3.14.0
```

- [ ] **Step 2: Create `.env.example`**

```
CLAUDE_API_KEY=your_claude_api_key_here
NOTIFICATION_EMAIL=you@example.com
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
token.json
credentials.json
*.log
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 4: Create `config.py`**

```python
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
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore config.py
git commit -m "feat: project scaffolding and config"
```

---

## Task 2: Logger

**Files:**
- Create: `logger.py`
- Create: `tests/test_logger.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_logger.py
import os
import json
import pytest
from logger import get_logger

@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    yield
    # nothing to clean — logger uses tmp file per test

def test_logger_writes_to_file(tmp_path):
    log_file = str(tmp_path / "test.log")
    logger = get_logger(log_file)
    logger.info("sender@test.com", "Test Subject", "פריקת מכולות", "replied")
    with open(log_file) as f:
        line = f.readline()
    assert "sender@test.com" in line
    assert "replied" in line

def test_logger_writes_error(tmp_path):
    log_file = str(tmp_path / "test.log")
    logger = get_logger(log_file)
    logger.error("fetch failed: timeout")
    with open(log_file) as f:
        line = f.readline()
    assert "ERROR" in line
    assert "fetch failed: timeout" in line
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_logger.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'logger'`

- [ ] **Step 3: Implement `logger.py`**

```python
import logging
import sys

def get_logger(log_file: str = "automation.log") -> "AutoLogger":
    return AutoLogger(log_file)

class AutoLogger:
    def __init__(self, log_file: str):
        self._logger = logging.getLogger(log_file)
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self._logger.addHandler(fh)

    def info(self, sender: str, subject: str, keyword: str, action: str):
        self._logger.info(f"sender={sender} subject={subject!r} keyword={keyword!r} action={action}")

    def warning(self, msg: str):
        self._logger.warning(f"WARNING {msg}")

    def error(self, msg: str):
        self._logger.error(f"ERROR {msg}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_logger.py -v
```

Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add logger.py tests/test_logger.py
git commit -m "feat: add file-based logger"
```

---

## Task 3: Detector

**Files:**
- Create: `detector.py`
- Create: `tests/test_detector.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_detector.py
from detector import contains_keyword, detect_language

# --- contains_keyword ---

def test_detects_hebrew_keyword():
    assert contains_keyword("אנו צריכים פריקת מכולות מחר") is True

def test_detects_hebrew_keyword_variant():
    assert contains_keyword("בקשה לפריקת המכולה") is True

def test_detects_english_keyword():
    assert contains_keyword("Please unload container at dock 3") is True

def test_detects_english_keyword_plural():
    assert contains_keyword("We need to unload containers today") is True

def test_no_match_returns_false():
    assert contains_keyword("Invoice attached for last shipment") is False

def test_case_insensitive_english():
    assert contains_keyword("Please UNLOAD CONTAINER asap") is True

def test_returns_matched_keyword():
    from detector import find_keyword
    assert find_keyword("פריקת מכולות בנמל") == "פריקת מכולות"

def test_returns_none_when_no_match():
    from detector import find_keyword
    assert find_keyword("no match here") is None

# --- detect_language ---

def test_detects_hebrew_language():
    assert detect_language("אנא פרקו את המכולה") == "Hebrew"

def test_detects_english_language():
    assert detect_language("Please unload container") == "English"

def test_mixed_prefers_hebrew():
    assert detect_language("unload container פריקת מכולות") == "Hebrew"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_detector.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'detector'`

- [ ] **Step 3: Implement `detector.py`**

```python
from config import KEYWORDS

def contains_keyword(text: str) -> bool:
    return find_keyword(text) is not None

def find_keyword(text: str) -> str | None:
    lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in lower:
            return kw
    return None

def detect_language(text: str) -> str:
    for ch in text:
        if "א" <= ch <= "ת":
            return "Hebrew"
    return "English"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_detector.py -v
```

Expected: `11 passed`

- [ ] **Step 5: Commit**

```bash
git add detector.py tests/test_detector.py
git commit -m "feat: add keyword detector and language detection"
```

---

## Task 4: Claude Client

**Files:**
- Create: `claude_client.py`
- Create: `tests/test_claude_client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_claude_client.py
import pytest
from unittest.mock import MagicMock, patch
from claude_client import generate_reply

SAMPLE_EMAIL = "We need to unload containers at pier 4 tomorrow morning."

def make_mock_response(content: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg

@patch("claude_client.anthropic.Anthropic")
def test_generate_reply_returns_subject_and_body(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response(
        '{"subject": "Re: Container Unloading Request", "body": "Dear customer, we confirm unloading at pier 4."}'
    )
    result = generate_reply(SAMPLE_EMAIL, "English")
    assert "subject" in result
    assert "body" in result
    assert isinstance(result["subject"], str)
    assert isinstance(result["body"], str)

@patch("claude_client.anthropic.Anthropic")
def test_generate_reply_passes_language(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response(
        '{"subject": "נושא", "body": "גוף ההודעה"}'
    )
    generate_reply("פריקת מכולות מחר", "Hebrew")
    call_kwargs = mock_client.messages.create.call_args
    prompt = str(call_kwargs)
    assert "Hebrew" in prompt

@patch("claude_client.anthropic.Anthropic")
def test_generate_reply_raises_on_invalid_json(mock_anthropic_class):
    mock_client = MagicMock()
    mock_anthropic_class.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_response("not valid json")
    with pytest.raises(ValueError, match="Claude returned invalid JSON"):
        generate_reply(SAMPLE_EMAIL, "English")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'claude_client'`

- [ ] **Step 3: Implement `claude_client.py`**

```python
import json
import anthropic
from config import CLAUDE_API_KEY, CLAUDE_MODEL

_PROMPT_TEMPLATE = """\
You are an assistant for a logistics company.
A customer sent an email about container unloading. Reply professionally in {language}.
Return ONLY a JSON object with exactly two keys: "subject" (reply subject line) and "body" (reply email body).
Do not include any text outside the JSON object.

Customer email:
{email_body}
"""

def generate_reply(email_body: str, language: str) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = _PROMPT_TEMPLATE.format(language=language, email_body=email_body)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw: {raw}") from e
    return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add claude_client.py tests/test_claude_client.py
git commit -m "feat: add Claude API client for reply generation"
```

---

## Task 5: Gmail Client

**Files:**
- Create: `gmail_client.py`
- Create: `tests/test_gmail_client.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gmail_client.py
import base64
import pytest
from unittest.mock import MagicMock, patch, call
from gmail_client import GmailClient

def make_service_mock():
    service = MagicMock()
    return service

def make_message(msg_id, sender, subject, body):
    raw_body = base64.urlsafe_b64encode(body.encode()).decode()
    return {
        "id": msg_id,
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Message-ID", "value": f"<{msg_id}@mail.test>"},
            ],
            "body": {"data": raw_body},
            "parts": [],
        },
    }

@patch("gmail_client.build_service")
def test_fetch_unread_returns_emails(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().list().execute.return_value = {
        "messages": [{"id": "abc123"}]
    }
    service.users().messages().get().execute.return_value = make_message(
        "abc123", "client@test.com", "Unload Request", "unload containers please"
    )
    client = GmailClient()
    emails = client.fetch_unread()
    assert len(emails) == 1
    assert emails[0]["sender"] == "client@test.com"
    assert emails[0]["subject"] == "Unload Request"
    assert "unload containers" in emails[0]["body"]

@patch("gmail_client.build_service")
def test_fetch_unread_returns_empty_when_none(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().list().execute.return_value = {}
    client = GmailClient()
    assert client.fetch_unread() == []

@patch("gmail_client.build_service")
def test_send_email_calls_api(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().send().execute.return_value = {"id": "sent1"}
    client = GmailClient()
    client.send_email(
        to="recipient@test.com",
        subject="Re: Unload",
        body="We confirm your request.",
        reply_to_id="<orig@mail.test>",
    )
    assert service.users().messages().send.called

@patch("gmail_client.build_service")
def test_mark_as_read_removes_unread_label(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    client = GmailClient()
    client.mark_as_read("msg123")
    service.users().messages().modify.assert_called_once_with(
        userId="me",
        id="msg123",
        body={"removeLabelIds": ["UNREAD"]},
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_gmail_client.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'gmail_client'`

- [ ] **Step 3: Implement `gmail_client.py`**

```python
import base64
import email as email_lib
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_gmail_client.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add gmail_client.py tests/test_gmail_client.py
git commit -m "feat: add Gmail API client"
```

---

## Task 6: Main Orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_main.py
import pytest
from unittest.mock import MagicMock, patch, call

MATCHING_EMAIL = {
    "id": "msg1",
    "sender": "client@test.com",
    "subject": "Unload Request",
    "message_id": "<msg1@mail.test>",
    "body": "Please unload containers at pier 4.",
}

NON_MATCHING_EMAIL = {
    "id": "msg2",
    "sender": "other@test.com",
    "subject": "Invoice",
    "message_id": "<msg2@mail.test>",
    "body": "Please find attached invoice.",
}

@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_processes_matching_email(mock_gmail, mock_claude, mock_logger):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.return_value = {
        "subject": "Re: Unload Request",
        "body": "We confirm your unloading request.",
    }
    from main import process_emails
    process_emails()
    mock_claude.generate_reply.assert_called_once()
    assert mock_gmail.send_email.call_count == 2  # reply + notification
    mock_gmail.mark_as_read.assert_called_once_with("msg1")

@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_skips_non_matching_email(mock_gmail, mock_claude, mock_logger):
    mock_gmail.fetch_unread.return_value = [NON_MATCHING_EMAIL]
    from main import process_emails
    process_emails()
    mock_claude.generate_reply.assert_not_called()
    mock_gmail.send_email.assert_not_called()
    mock_gmail.mark_as_read.assert_not_called()

@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_claude_failure_leaves_email_unread(mock_gmail, mock_claude, mock_logger):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.side_effect = Exception("API error")
    from main import process_emails
    process_emails()
    mock_gmail.send_email.assert_not_called()
    mock_gmail.mark_as_read.assert_not_called()

@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_notification_failure_does_not_block_reply(mock_gmail, mock_claude, mock_logger):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.return_value = {
        "subject": "Re: Unload",
        "body": "Confirmed.",
    }
    # First send_email (reply) succeeds, second (notification) fails
    mock_gmail.send_email.side_effect = [None, Exception("notify failed")]
    from main import process_emails
    process_emails()
    mock_gmail.mark_as_read.assert_called_once_with("msg1")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement `main.py`**

```python
import time
import importlib
import config
from detector import contains_keyword, find_keyword, detect_language
from logger import get_logger
import gmail_client as _gmail_module
import claude_client as _claude_module

logger = get_logger(config.LOG_FILE)

# Module-level references allow test patching
gmail = _gmail_module.GmailClient()
claude_client = _claude_module


def process_emails():
    try:
        emails = gmail.fetch_unread()
    except Exception as e:
        logger.error(f"Gmail fetch failed: {e}")
        return

    for email in emails:
        keyword = find_keyword(email["body"])
        if not keyword:
            continue

        language = detect_language(email["body"])

        try:
            reply = claude_client.generate_reply(email["body"], language)
        except Exception as e:
            logger.error(f"Claude failed for {email['sender']}: {e}")
            continue

        try:
            gmail.send_email(
                to=email["sender"],
                subject=reply["subject"],
                body=reply["body"],
                reply_to_id=email["message_id"],
            )
        except Exception as e:
            logger.error(f"Reply send failed for {email['sender']}: {e}")
            continue

        try:
            gmail.send_email(
                to=config.NOTIFICATION_EMAIL,
                subject=f"[Auto-Reply Sent] {email['subject']}",
                body=(
                    f"Auto-reply sent to: {email['sender']}\n"
                    f"Original subject: {email['subject']}\n"
                    f"Keyword matched: {keyword}\n\n"
                    f"--- Reply preview ---\n{reply['body'][:500]}"
                ),
            )
        except Exception as e:
            logger.warning(f"Notification failed for {email['sender']}: {e}")

        try:
            gmail.mark_as_read(email["id"])
        except Exception as e:
            logger.error(f"Mark-as-read failed for {email['id']}: {e}")

        logger.info(email["sender"], email["subject"], keyword, "replied")


if __name__ == "__main__":
    print(f"Starting Gmail automation. Polling every {config.POLL_INTERVAL_MINUTES} min.")
    while True:
        process_emails()
        time.sleep(config.POLL_INTERVAL_MINUTES * 60)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_main.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main orchestrator with full error handling"
```

---

## Task 7: Gmail OAuth Setup (Manual Steps)

This task is manual — must be done once before first run.

- [ ] **Step 1: Create Google Cloud project**

1. Go to https://console.cloud.google.com/
2. Create new project (e.g. `gmail-automation`)
3. Enable **Gmail API**: APIs & Services → Enable APIs → search "Gmail API" → Enable

- [ ] **Step 2: Create OAuth credentials**

1. APIs & Services → Credentials → Create Credentials → OAuth client ID
2. Application type: **Desktop app**
3. Download JSON → rename to `credentials.json` → place in project root

- [ ] **Step 3: Add test user (if app not verified)**

1. OAuth consent screen → Test users → add your Gmail address

- [ ] **Step 4: Create `.env` from template**

```bash
cp .env.example .env
```

Edit `.env`:
```
CLAUDE_API_KEY=sk-ant-...your key...
NOTIFICATION_EMAIL=your@email.com
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

- [ ] **Step 5: First run (triggers browser OAuth flow)**

```bash
python main.py
```

Browser opens → sign in with Gmail → grant permissions → `token.json` created.
Script starts polling. Stop with `Ctrl+C` after verifying no errors.

---

## Task 8: Cron Setup (Windows Task Scheduler)

- [ ] **Step 1: Create scheduled task**

Open PowerShell as Administrator:

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\projects\gmail-automatization\main.py" -WorkingDirectory "C:\projects\gmail-automatization"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Register-ScheduledTask -TaskName "GmailAutomation" -Action $action -Trigger $trigger -RunLevel Highest
```

- [ ] **Step 2: Verify task runs**

```powershell
Start-ScheduledTask -TaskName "GmailAutomation"
Start-Sleep -Seconds 10
Get-ScheduledTaskInfo -TaskName "GmailAutomation"
```

Expected: `LastTaskResult: 0` (success).

- [ ] **Step 3: Check log**

```bash
tail -20 automation.log
```

Expected: timestamps and poll cycle entries, no ERROR lines.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "docs: finalize setup notes in plan"
```

---

## Spec Coverage Check

| Spec requirement | Task |
|-----------------|------|
| Keyword: `פריקת מכולות` | Task 3 |
| Keyword: `פריקת המכולה` | Task 3 |
| Keyword: `unload container/s` | Task 3 |
| Language detection (Hebrew/English) | Task 3 |
| Claude-generated reply | Task 4 |
| Send reply to sender | Task 6 |
| Send notification to config email | Task 6 |
| Mark email as read | Task 5 + 6 |
| Error handling: Claude fail → leave unread | Task 6 |
| Error handling: notify fail → don't block | Task 6 |
| Config file with all values | Task 1 |
| File-based logging | Task 2 |
| Cron polling | Task 8 |
