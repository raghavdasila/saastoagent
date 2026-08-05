from __future__ import annotations

import asyncio
import smtplib
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from typing import Protocol, runtime_checkable

from .config import AuthSettings


class MailDeliveryUnavailable(RuntimeError):
    pass


class MailRecipientRejected(RuntimeError):
    pass


@dataclass
class MailServiceAvailability:
    unavailable_until: float = 0.0

    @property
    def known_unavailable(self) -> bool:
        return time.monotonic() < self.unavailable_until

    def mark_available(self) -> None:
        self.unavailable_until = 0.0

    def mark_unavailable(self, retry_after_seconds: float = 30.0) -> None:
        self.unavailable_until = time.monotonic() + retry_after_seconds


@runtime_checkable
class OwnerMailDelivery(Protocol):
    @property
    def known_unavailable(self) -> bool: ...

    async def send_verification(self, recipient: str, link: str) -> None: ...

    async def send_password_reset(self, recipient: str, link: str) -> None: ...


class UnconfiguredMailDelivery:
    """Explicit failure used when the Gmail credential is not configured."""

    @property
    def known_unavailable(self) -> bool:
        return True

    async def send_verification(self, recipient: str, link: str) -> None:
        del recipient, link
        raise MailDeliveryUnavailable("Gmail SMTP is not configured.")

    async def send_password_reset(self, recipient: str, link: str) -> None:
        del recipient, link
        raise MailDeliveryUnavailable("Gmail SMTP is not configured.")


@dataclass(frozen=True)
class GmailSmtpMailDelivery:
    host: str
    port: int
    username: str
    from_address: str
    app_password: str
    timeout_seconds: float
    availability: MailServiceAvailability = field(
        default_factory=MailServiceAvailability,
        compare=False,
        repr=False,
    )

    @property
    def known_unavailable(self) -> bool:
        return self.availability.known_unavailable

    @classmethod
    def from_settings(cls, settings: AuthSettings) -> GmailSmtpMailDelivery:
        password = (
            settings.smtp_app_password.get_secret_value()
            if settings.smtp_app_password is not None
            else ""
        )
        if not password:
            raise ValueError("Gmail SMTP App Password is required.")
        if not settings.smtp_starttls:
            raise ValueError("Gmail SMTP delivery requires STARTTLS.")
        return cls(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            from_address=settings.smtp_from_address,
            app_password=password,
            timeout_seconds=settings.smtp_timeout_seconds,
        )

    async def send_verification(self, recipient: str, link: str) -> None:
        await self._deliver(
            recipient,
            subject="Verify your Corpus email",
            body=(
                "Verify your Corpus owner email by opening this link:\n\n"
                f"{link}\n\n"
                "This link expires in 24 hours."
            ),
        )

    async def send_password_reset(self, recipient: str, link: str) -> None:
        await self._deliver(
            recipient,
            subject="Reset your Corpus password",
            body=(
                "Reset your Corpus owner password by opening this link:\n\n"
                f"{link}\n\n"
                "This link expires in one hour. If you did not request this, ignore this email."
            ),
        )

    async def _deliver(self, recipient: str, *, subject: str, body: str) -> None:
        try:
            await asyncio.to_thread(
                self._deliver_sync,
                recipient,
                subject,
                body,
            )
        except smtplib.SMTPRecipientsRefused as error:
            raise MailRecipientRejected("The recipient rejected the message.") from error
        except (OSError, TimeoutError, smtplib.SMTPException) as error:
            self.availability.mark_unavailable()
            raise MailDeliveryUnavailable("Gmail SMTP delivery failed.") from error
        self.availability.mark_available()

    def _deliver_sync(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.from_address
        message["To"] = recipient
        message["Date"] = format_datetime(datetime.now(timezone.utc))
        message["Message-ID"] = make_msgid(domain=self.from_address.partition("@")[2])
        message.set_content(body)

        with smtplib.SMTP(
            self.host,
            self.port,
            timeout=self.timeout_seconds,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(self.username, self.app_password)
            refused = smtp.send_message(
                message,
                from_addr=self.from_address,
                to_addrs=[recipient],
            )
        if refused:
            raise smtplib.SMTPRecipientsRefused(refused)


def create_mail_delivery(settings: AuthSettings) -> OwnerMailDelivery:
    password = (
        settings.smtp_app_password.get_secret_value()
        if settings.smtp_app_password is not None
        else ""
    )
    if not password:
        return UnconfiguredMailDelivery()
    return GmailSmtpMailDelivery.from_settings(settings)


__all__ = [
    "GmailSmtpMailDelivery",
    "MailDeliveryUnavailable",
    "MailRecipientRejected",
    "MailServiceAvailability",
    "OwnerMailDelivery",
    "UnconfiguredMailDelivery",
    "create_mail_delivery",
]
