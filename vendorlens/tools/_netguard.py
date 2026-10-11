"""Network guard: strict host validation and SSRF protection.

The public Lambda handler and the homepage fetching tool both turn
user-supplied strings into ``https://<host>/`` requests. Without validation a
value containing a path, a port, userinfo or an IP literal could be used to
reach internal services. These helpers normalize to a bare apex host, reject
anything that is not a public DNS name, and re-check resolved addresses so a
redirect cannot pivot to a private range.
"""
from __future__ import annotations

import ipaddress
import re
import socket

# A strict bare hostname: dot-separated labels, letters/digits/hyphens,
# no IP literals, ports, userinfo, paths or scheme.
_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$")


def _idna(value: str) -> str | None:
    """Lowercase and punycode-normalize. Returns None on any error."""
    try:
        return value.encode("idna").decode("ascii").lower()
    except Exception:
        return None


def normalize_domain(value: str) -> str | None:
    """Return a canonical bare domain, or None if the value is not one.

    Rejects anything with a scheme, path, port, userinfo, whitespace, an IP
    literal, a single label, or an all-numeric final label.
    """
    if not isinstance(value, str):
        return None
    v = value.strip().lower()
    if not v:
        return None
    # No scheme, path, query, fragment, port, userinfo, backslash or spaces.
    if any(ch in v for ch in "/ : @ ? # \\ \t\n\r"):
        return None
    v = v.rstrip(".")
    if v.startswith("."):
        return None
    host = _idna(v)
    if not host or not _DOMAIN_RE.match(host):
        return None
    # Explicitly reject IP literals that happen to look dotted.
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        pass
    last = host.rsplit(".", 1)[-1]
    if "." not in host or last.isdigit() or len(last) < 2:
        return None
    return host


def ip_is_disallowed(ip: ipaddress._BaseAddress) -> bool:
    """True when an address must never be fetched (private/internal)."""
    return (ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def host_is_public(host: str) -> bool:
    """Resolve `host` and return True only if *every* address is public and
    routable. A domain that fails to resolve is treated as not safe."""
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    if not infos:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if ip_is_disallowed(ip):
            return False
    return True


def host_from_url(url: str) -> str | None:
    """Extract a bare, normalized host from an absolute URL (or None)."""
    from urllib.parse import urlsplit
    try:
        parts = urlsplit(url if "://" in url else f"https://{url}")
    except Exception:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    return normalize_domain(parts.hostname or "")
