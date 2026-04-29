import time
import config
from detector import find_keyword, detect_language
from logger import get_logger
import gmail_client as _gmail_module
import claude_client as _claude_module

logger = get_logger(config.LOG_FILE)
gmail = None  # initialized on first call; tests patch this directly
claude_client = _claude_module


def process_emails():
    global gmail
    if gmail is None:
        gmail = _gmail_module.GmailClient()

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
