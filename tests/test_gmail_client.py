# tests/test_gmail_client.py
import base64
import pytest
from unittest.mock import MagicMock, patch
from gmail_client import GmailClient

def make_service_mock():
    return MagicMock()

def make_message(msg_id, sender, subject, body):
    raw_body = base64.urlsafe_b64encode(body.encode()).decode()
    return {
        "id": msg_id,
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
                {"name": "Message-ID", "value": f"<{msg_id}@mail.test>"},
            ],
            "body": {"data": raw_body},
            "parts": [],
        },
    }

@patch("gmail_client.build_service")
def test_fetch_unread_returns_emails(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().list().execute.return_value = {
        "messages": [{"id": "abc123"}]
    }
    service.users().messages().get().execute.return_value = make_message(
        "abc123", "client@test.com", "Unload Request", "unload containers please"
    )
    client = GmailClient()
    emails = client.fetch_unread()
    assert len(emails) == 1
    assert emails[0]["sender"] == "client@test.com"
    assert emails[0]["subject"] == "Unload Request"
    assert "unload containers" in emails[0]["body"]

@patch("gmail_client.build_service")
def test_fetch_unread_returns_empty_when_none(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().list().execute.return_value = {}
    client = GmailClient()
    assert client.fetch_unread() == []

@patch("gmail_client.build_service")
def test_send_email_calls_api(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    service.users().messages().send().execute.return_value = {"id": "sent1"}
    client = GmailClient()
    client.send_email(
        to="recipient@test.com",
        subject="Re: Unload",
        body="We confirm your request.",
        reply_to_id="<orig@mail.test>",
    )
    assert service.users().messages().send.called

@patch("gmail_client.build_service")
def test_mark_as_read_removes_unread_label(mock_build):
    service = make_service_mock()
    mock_build.return_value = service
    client = GmailClient()
    client.mark_as_read("msg123")
    service.users().messages().modify.assert_called_once_with(
        userId="me",
        id="msg123",
        body={"removeLabelIds": ["UNREAD"]},
    )
