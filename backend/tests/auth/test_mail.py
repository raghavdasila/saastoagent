from __future__ import annotations

import asyncio
import smtplib

import pytest

from corpus.auth.config import AuthSettings
from corpus.auth.mail import (
    GmailSmtpMailDelivery,
    MailDeliveryUnavailable,
    UnconfiguredMailDelivery,
    create_mail_delivery,
)


class RecordingSmtp:
    instances: list["RecordingSmtp"] = []

    def __init__(self, host: str, port: int, *, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_credentials: tuple[str, str] | None = None
        self.message = None
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def ehlo(self) -> tuple[int, bytes]:
        return 250, b"ok"

    def starttls(self, *, context) -> tuple[int, bytes]:
        assert context is not None
        self.started_tls = True
        return 220, b"ready"

    def login(self, username: str, password: str) -> tuple[int, bytes]:
        self.login_credentials = (username, password)
        return 235, b"accepted"

    def send_message(self, message, *, from_addr: str, to_addrs: list[str]):
        self.message = (message, from_addr, to_addrs)
        return {}


def _settings(*, password: str | None) -> AuthSettings:
    return AuthSettings(
        reset_secret="r" * 40,
        verification_secret="v" * 40,
        public_frontend_url="http://127.0.0.1:5199",
        smtp_username="no-reply@saastoagent.com",
        smtp_from_address="no-reply@saastoagent.com",
        smtp_app_password=password,
    )


def test_gmail_delivery_uses_starttls_and_sends_verification_link(monkeypatch) -> None:
    RecordingSmtp.instances.clear()
    monkeypatch.setattr(smtplib, "SMTP", RecordingSmtp)
    delivery = GmailSmtpMailDelivery.from_settings(_settings(password="p" * 16))

    asyncio.run(
        delivery.send_verification(
            "owner@example.com",
            "http://127.0.0.1:5199/verify#token=secret-token",
        )
    )

    smtp = RecordingSmtp.instances[0]
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 587
    assert smtp.started_tls is True
    assert smtp.login_credentials == ("no-reply@saastoagent.com", "p" * 16)
    message, from_addr, to_addrs = smtp.message
    assert message["Subject"] == "Verify your Corpus email"
    assert "verify#token=secret-token" in message.get_content()
    assert from_addr == "no-reply@saastoagent.com"
    assert to_addrs == ["owner@example.com"]


def test_gmail_delivery_maps_smtp_failures_to_explicit_unavailability(
    monkeypatch,
) -> None:
    class RejectedSmtp(RecordingSmtp):
        def login(self, username: str, password: str):
            del username, password
            raise smtplib.SMTPAuthenticationError(535, b"rejected")

    monkeypatch.setattr(smtplib, "SMTP", RejectedSmtp)
    delivery = GmailSmtpMailDelivery.from_settings(_settings(password="p" * 16))

    with pytest.raises(MailDeliveryUnavailable, match="Gmail SMTP delivery failed"):
        asyncio.run(
            delivery.send_password_reset(
                "owner@example.com",
                "http://127.0.0.1:5199/reset-password#token=secret-token",
            )
        )


def test_mail_factory_requires_an_explicit_smtp_credential() -> None:
    assert isinstance(create_mail_delivery(_settings(password=None)), UnconfiguredMailDelivery)
    assert isinstance(
        create_mail_delivery(_settings(password="p" * 16)),
        GmailSmtpMailDelivery,
    )
