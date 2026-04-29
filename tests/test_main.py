# tests/test_main.py
import pytest
from unittest.mock import MagicMock, patch

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

@patch("main.is_whitelisted", return_value=False)
@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_processes_matching_email(mock_gmail, mock_claude, mock_logger, mock_wl):
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

@patch("main.is_whitelisted", return_value=False)
@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_skips_non_matching_email(mock_gmail, mock_claude, mock_logger, mock_wl):
    mock_gmail.fetch_unread.return_value = [NON_MATCHING_EMAIL]
    from main import process_emails
    process_emails()
    mock_claude.generate_reply.assert_not_called()
    mock_gmail.send_email.assert_not_called()
    mock_gmail.mark_as_read.assert_not_called()

@patch("main.is_whitelisted", return_value=False)
@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_claude_failure_leaves_email_unread(mock_gmail, mock_claude, mock_logger, mock_wl):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.side_effect = Exception("API error")
    from main import process_emails
    process_emails()
    mock_gmail.send_email.assert_not_called()
    mock_gmail.mark_as_read.assert_not_called()

@patch("main.is_whitelisted", return_value=False)
@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_notification_failure_does_not_block_reply(mock_gmail, mock_claude, mock_logger, mock_wl):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.return_value = {
        "subject": "Re: Unload",
        "body": "Confirmed.",
    }
    mock_gmail.send_email.side_effect = [None, Exception("notify failed")]
    from main import process_emails
    process_emails()
    mock_gmail.mark_as_read.assert_called_once_with("msg1")

@patch("main.is_whitelisted", return_value=True)
@patch("main.logger")
@patch("main.claude_client")
@patch("main.gmail")
def test_whitelisted_sender_gets_pricing(mock_gmail, mock_claude, mock_logger, mock_wl):
    mock_gmail.fetch_unread.return_value = [MATCHING_EMAIL]
    mock_claude.generate_reply.return_value = {
        "subject": "Re: Unload Request",
        "body": "20ft=700 NIS, 40ft=900 NIS.",
    }
    from main import process_emails
    process_emails()
    call_kwargs = mock_claude.generate_reply.call_args
    assert call_kwargs.kwargs.get("include_pricing") is True
