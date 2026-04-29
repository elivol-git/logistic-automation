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
