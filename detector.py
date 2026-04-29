import re
from config import KEYWORDS, GCS_SERVICE_ACCOUNT_FILE, WHITELIST_GCS_BUCKET, WHITELIST_GCS_BLOB

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

def load_whitelist() -> set[str]:
    from google.cloud import storage
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(GCS_SERVICE_ACCOUNT_FILE)
    client = storage.Client(credentials=creds)
    bucket = client.bucket(WHITELIST_GCS_BUCKET)
    blob = bucket.blob(WHITELIST_GCS_BLOB)
    content = blob.download_as_text(encoding="utf-8")
    return {
        line.strip().lower()
        for line in content.splitlines()
        if line.strip() and not line.startswith("#")
    }

def extract_email(sender: str) -> str:
    match = re.search(r"<(.+?)>", sender)
    return match.group(1).lower() if match else sender.strip().lower()

def is_whitelisted(sender: str) -> bool:
    return extract_email(sender) in load_whitelist()
