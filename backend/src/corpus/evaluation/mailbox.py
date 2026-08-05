from __future__ import annotations

import asyncio
import re
import secrets
import string
import time
from dataclasses import dataclass

import httpx


class MailboxEvaluationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MailboxMessage:
    id: str
    subject: str
    text: str

    def first_link(self, path: str) -> str:
        match = re.search(rf"https?://[^\s<>]+{re.escape(path)}#token=[^\s<>]+", self.text)
        if match is None:
            raise MailboxEvaluationError(
                f"Mailbox message did not contain the expected {path} link."
            )
        return match.group(0).rstrip(".,)")


class MailTmMailbox:
    """Disposable public mailbox used only by explicit product evaluations.

    Mail.tm requires attribution and limits clients to eight requests per second.
    This adapter deliberately polls once per second and never enters product code.
    """

    api_url = "https://api.mail.tm"

    def __init__(self, client: httpx.AsyncClient, address: str, password: str, account_id: str, token: str) -> None:
        self._client = client
        self.address = address
        self._password = password
        self._account_id = account_id
        self._token = token

    @classmethod
    async def create(cls) -> MailTmMailbox:
        client = httpx.AsyncClient(
            timeout=20.0,
            headers={"User-Agent": "Corpus-Product-Evaluation/1.0"},
        )
        try:
            domains_response = await client.get(f"{cls.api_url}/domains?page=1")
            domains_response.raise_for_status()
            domains = domains_response.json().get("hydra:member", [])
            if not domains:
                raise MailboxEvaluationError("Mail.tm returned no available domains.")
            address = f"corpus-eval-{_random_text(14)}@{domains[0]['domain']}"
            password = f"C0rpus-{_random_text(28)}!"
            created = None
            for attempt in range(4):
                created = await client.post(
                    f"{cls.api_url}/accounts",
                    json={"address": address, "password": password},
                )
                if created.status_code != 429:
                    break
                await asyncio.sleep(5.0 * (attempt + 1))
            assert created is not None
            created.raise_for_status()
            account_id = created.json()["id"]
            authenticated = await client.post(
                f"{cls.api_url}/token",
                json={"address": address, "password": password},
            )
            authenticated.raise_for_status()
            return cls(
                client,
                address,
                password,
                account_id,
                authenticated.json()["token"],
            )
        except Exception:
            await client.aclose()
            raise

    async def wait_for_message(
        self,
        *,
        subject: str,
        after: float,
        timeout_seconds: float = 90.0,
    ) -> MailboxMessage:
        deadline = time.monotonic() + timeout_seconds
        headers = self._headers()
        while time.monotonic() < deadline:
            listing = await self._client.get(
                f"{self.api_url}/messages?page=1", headers=headers
            )
            listing.raise_for_status()
            for item in listing.json().get("hydra:member", []):
                if item.get("subject") != subject:
                    continue
                created_at = item.get("createdAt")
                if created_at is not None and _iso_timestamp(created_at) < after:
                    continue
                detail = await self._client.get(
                    f"{self.api_url}/messages/{item['id']}", headers=headers
                )
                detail.raise_for_status()
                payload = detail.json()
                return MailboxMessage(
                    id=payload["id"],
                    subject=payload.get("subject", ""),
                    text=payload.get("text") or "",
                )
            await asyncio.sleep(1.0)
        raise MailboxEvaluationError(
            f"Mail.tm did not receive {subject!r} within {timeout_seconds:.0f} seconds."
        )

    async def close(self) -> None:
        try:
            response = await self._client.delete(
                f"{self.api_url}/accounts/{self._account_id}",
                headers=self._headers(),
            )
            if response.status_code != 204:
                raise MailboxEvaluationError(
                    f"Mail.tm mailbox cleanup returned HTTP {response.status_code}."
                )
        finally:
            await self._client.aclose()

    async def __aenter__(self) -> MailTmMailbox:
        return self

    async def __aexit__(self, _type, _value, _traceback) -> None:
        await self.close()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}


def _random_text(length: int) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _iso_timestamp(value: str) -> float:
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


__all__ = [
    "MailboxEvaluationError",
    "MailboxMessage",
    "MailTmMailbox",
]
