# Gmail Auto-Reply Automation — Design Spec

**Date:** 2026-04-29  
**Project:** Gmail automation for logistics company  
**Status:** Approved

---

## Overview

Python service that polls Gmail every 5 minutes, detects emails about container unloading (Hebrew keywords), generates a context-aware reply using Claude API, sends the reply to the original sender, and notifies a configured email address.

---

## Architecture

```
Cron (every 5 min)
    └─► main.py
         ├─► Gmail API — fetch unread emails
         ├─► keyword detector — scan body for keywords
         ├─► language detector — Hebrew or English?
         ├─► Claude API — generate subject + reply body
         ├─► Gmail API — send reply to original sender
         ├─► Gmail API — send notification to NOTIFICATION_EMAIL
         └─► Gmail API — mark email as read
```

---

## Components

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point, orchestrates full flow |
| `gmail_client.py` | Gmail API wrapper: fetch unread, send, mark read |
| `detector.py` | Keyword matching + language detection |
| `claude_client.py` | Claude API call, structured prompt, returns subject + body |
| `config.py` | All configurable values |
| `.env` | Secrets: Gmail OAuth credentials, Claude API key |
| `logger.py` | File-based logging |

---

## Data Flow

1. Fetch unread emails from inbox
2. For each email: check body for keywords (case-insensitive, partial match)
3. If match detected:
   - Detect language: Hebrew chars present → Hebrew reply, else English reply
   - Call Claude with prompt: *"You are a logistics company assistant. Reply to this container unloading inquiry in {language}. Structure: subject line + professional body."*
   - Send reply to original sender
   - Send notification to `NOTIFICATION_EMAIL` with: original sender, original subject, generated reply preview
   - Mark original email as read
4. If no match: skip, leave unread

---

## Rules / Trigger Cases

**Case 1:**  
- Keywords: `פריקת מכולות`, `פריקת המכולה`, `unload container`, `unload containers`  
- Action: auto-reply + notify

*(More cases to be added in future iterations)*

---

## Configuration (`config.py`)

```python
KEYWORDS = ["פריקת מכולות", "פריקת המכולה", "unload container", "unload containers"]
NOTIFICATION_EMAIL = "you@example.com"
POLL_INTERVAL_MINUTES = 5
CLAUDE_MODEL = "claude-sonnet-4-6"
REPLY_STRUCTURE = "subject + professional body, logistics context"
```

---

## Error Handling

| Failure | Behavior |
|---------|----------|
| Gmail API fetch fails | Log error, retry next cycle |
| Claude API fails | Log error, skip reply, leave email unread (retry next cycle) |
| Reply send fails | Log error, retry next cycle |
| Notification send fails | Log warning, do not block main reply flow |

---

## Logging

File-based log. Each entry: timestamp, sender email, subject, keyword matched, action taken (replied / skipped / error).

---

## Dependencies

- `google-auth`, `google-api-python-client` — Gmail API
- `anthropic` — Claude API
- `python-dotenv` — env var loading
- `langdetect` or char-range check — language detection

---

## Out of Scope

- Web UI or dashboard
- Database / persistence layer
- Real-time webhook (polling only)
- Multi-account support
