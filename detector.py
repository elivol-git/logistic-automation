import re
from config import KEYWORDS, AWS_REGION, SSM_WHITELIST_PARAM

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
    import boto3, json
    client = boto3.client("ssm", region_name=AWS_REGION)
    r = client.get_parameter(Name=SSM_WHITELIST_PARAM)
    emails = json.loads(r["Parameter"]["Value"])
    return {e.strip().lower() for e in emails}

def extract_email(sender: str) -> str:
    match = re.search(r"<(.+?)>", sender)
    return match.group(1).lower() if match else sender.strip().lower()

def is_whitelisted(sender: str) -> bool:
    return extract_email(sender) in load_whitelist()
