# tests/test_detector.py
from detector import contains_keyword, detect_language

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

def test_detects_hebrew_language():
    assert detect_language("אנא פרקו את המכולה") == "Hebrew"

def test_detects_english_language():
    assert detect_language("Please unload container") == "English"

def test_mixed_prefers_hebrew():
    assert detect_language("unload container פריקת מכולות") == "Hebrew"
