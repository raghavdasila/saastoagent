from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class MedusaCreds:
    email: str
    password: str
    backend_url: str
    publishable_api_key: str


def line_value(text: str, label: str) -> str:
    match = re.search(rf"- {re.escape(label)}:\s*(.+)", text)
    if not match:
        raise ValueError(f"Missing {label} in CREDS.md")
    return match.group(1).strip()


def parse_creds(path: Path) -> MedusaCreds:
    text = path.read_text(encoding="utf-8")
    return MedusaCreds(
        email=line_value(text, "Email"),
        password=line_value(text, "Password"),
        backend_url=line_value(text, "Backend URL").rstrip("/"),
        publishable_api_key=line_value(text, "Publishable API key"),
    )


def request_json(url: str, method: str = "GET", headers: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload) if payload else {}


def run_medusa_smoke(creds_path: Path, base_url: str | None = None) -> dict[str, Any]:
    creds = parse_creds(creds_path)
    backend = (base_url or creds.backend_url).rstrip("/")
    result: dict[str, Any] = {"backend_url": backend, "checks": []}
    try:
        status, auth_payload = request_json(
            f"{backend}/auth/user/emailpass",
            method="POST",
            body={"email": creds.email, "password": creds.password},
        )
        token = auth_payload.get("token") or auth_payload.get("jwt") or auth_payload.get("access_token")
        result["checks"].append({"name": "admin_auth", "status": status, "ok": bool(token)})
        admin_status, admin_payload = request_json(
            f"{backend}/admin/products",
            headers={"Authorization": f"Bearer {token}"},
        )
        result["checks"].append({"name": "admin_products", "status": admin_status, "ok": admin_status < 400, "keys": sorted(admin_payload)[:8] if isinstance(admin_payload, dict) else []})
        store_status, store_payload = request_json(
            f"{backend}/store/products",
            headers={"x-publishable-api-key": creds.publishable_api_key},
        )
        result["checks"].append({"name": "store_products", "status": store_status, "ok": store_status < 400, "keys": sorted(store_payload)[:8] if isinstance(store_payload, dict) else []})
    except (HTTPError, URLError, ValueError) as exc:
        result["checks"].append({"name": "exception", "ok": False, "error": str(exc)})
    result["ok"] = all(check.get("ok") for check in result["checks"])
    return result
