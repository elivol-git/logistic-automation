import time
import os
import config
from detector import find_keyword, detect_language
from logger import get_logger
import gmail_client as _gmail_module
import claude_client as _claude_module

LAST_RUN_FILE = "last_run.txt"

def _read_last_run() -> int | None:
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE) as f:
            return int(f.read().strip())
    return None

def _save_last_run(ts: int):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(str(ts))

logger = get_logger(config.LOG_FILE)
gmail = None  # initialized on first call; tests patch this directly
claude_client = _claude_module


def process_emails():
    global gmail
    if gmail is None:
        print("Connecting to Gmail...")
        gmail = _gmail_module.GmailClient()
        print("Connected.")

    last_run = _read_last_run()
    now = int(time.time())
    if last_run:
        import datetime
        since = datetime.datetime.fromtimestamp(last_run).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Fetching unread emails since last run ({since})...")
    else:
        print("Fetching unread emails (first run — no time filter)...")
    try:
        emails = gmail.fetch_unread(after_timestamp=last_run)
    except Exception as e:
        print(f"ERROR: Gmail fetch failed: {e}")
        logger.error(f"Gmail fetch failed: {e}")
        return
    _save_last_run(now)

    print(f"Found {len(emails)} unread email(s).")

    for email in emails:
        keyword = find_keyword(email["body"])
        if not keyword:
            print(f"  SKIP: {email['sender']} — no keyword match")
            continue

        language = detect_language(email["body"])
        print(f"  MATCH: {email['sender']} | keyword='{keyword}' | lang={language}")

        print(f"  Generating reply with Claude...")
        try:
            reply = claude_client.generate_reply(email["body"], language)
        except Exception as e:
            print(f"  ERROR: Claude failed: {e}")
            logger.error(f"Claude failed for {email['sender']}: {e}")
            continue

        print(f"  Sending reply to {email['sender']}...")
        try:
            gmail.send_email(
                to=email["sender"],
                subject=reply["subject"],
                body=reply["body"],
                reply_to_id=email["message_id"],
            )
            print(f"  Reply sent. Subject: {reply['subject']}")
        except Exception as e:
            print(f"  ERROR: Reply send failed: {e}")
            logger.error(f"Reply send failed for {email['sender']}: {e}")
            continue

        print(f"  Sending notification to {config.NOTIFICATION_EMAIL}...")
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
            print(f"  Notification sent.")
        except Exception as e:
            print(f"  WARNING: Notification failed: {e}")
            logger.warning(f"Notification failed for {email['sender']}: {e}")

        try:
            gmail.mark_as_read(email["id"])
            print(f"  Marked as read.")
        except Exception as e:
            print(f"  ERROR: Mark-as-read failed: {e}")
            logger.error(f"Mark-as-read failed for {email['id']}: {e}")

        logger.info(email["sender"], email["subject"], keyword, "replied")
        print(f"  Done.")


if __name__ == "__main__":
    print(f"Starting Gmail automation. Polling every {config.POLL_INTERVAL_MINUTES} min. Press Ctrl+C to stop.")
    while True:
        import datetime
        print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] --- Poll cycle ---")
        process_emails()
        print(f"Sleeping {config.POLL_INTERVAL_MINUTES} min...")
        time.sleep(config.POLL_INTERVAL_MINUTES * 60)
