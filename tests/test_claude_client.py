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
