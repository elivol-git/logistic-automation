import re
from config import KEYWORDS

WHITELIST_FILE = "whitelist.txt"

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
    try:
        with open(WHITELIST_FILE, encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.startswith("#")
            }
    except FileNotFoundError:
        return set()

def extract_email(sender: str) -> str:
    match = re.search(r"<(.+?)>", sender)
    return match.group(1).lower() if match else sender.strip().lower()

def is_whitelisted(sender: str) -> bool:
    return extract_email(sender) in load_whitelist()
