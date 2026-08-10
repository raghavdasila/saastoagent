from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from .contracts import NetworkPolicy
from .errors import NetworkPolicyError


async def enforce_network_policy(url: str, policy: NetworkPolicy) -> None:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise NetworkPolicyError(
            "network_scheme_forbidden",
            "The API URL must use HTTP or HTTPS.",
        )
    if scheme == "http" and not policy.allow_http:
        raise NetworkPolicyError(
            "insecure_http_forbidden",
            "This connection does not permit unencrypted HTTP.",
        )
    if parsed.username or parsed.password:
        raise NetworkPolicyError(
            "url_userinfo_forbidden",
            "Credentials cannot be embedded in the API URL.",
        )
    if not parsed.hostname:
        raise NetworkPolicyError("network_host_missing", "The API host is missing.")

    try:
        addresses = await asyncio.to_thread(_resolve_addresses, parsed.hostname, parsed.port)
    except OSError as error:
        raise NetworkPolicyError(
            "network_host_unresolved",
            "The configured API host could not be resolved.",
        ) from error
    if not addresses:
        raise NetworkPolicyError(
            "network_host_unresolved",
            "The configured API host could not be resolved.",
        )
    allowed_networks = tuple(
        ipaddress.ip_network(value, strict=False) for value in policy.allowed_private_cidrs
    )
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if _public(ip) or policy.allow_private_networks:
            continue
        if any(ip in network for network in allowed_networks):
            continue
        raise NetworkPolicyError(
            "private_network_forbidden",
            "The configured API host resolves to a forbidden network.",
        )


def _resolve_addresses(host: str, port: int | None) -> set[str]:
    try:
        return {str(ipaddress.ip_address(host))}
    except ValueError:
        pass
    return {
        item[4][0]
        for item in socket.getaddrinfo(host, port or 443, type=socket.SOCK_STREAM)
    }


def _public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )

