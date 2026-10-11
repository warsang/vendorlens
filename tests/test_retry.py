"""Retry classification: only transient failures are retried (P1.3)."""
from vendorlens.tools import _http


def test_transient_cases():
    for msg in [
        "HTTPStatusError: Server error '502 Bad Gateway'",
        "HTTPStatusError: Server error '503 Service Unavailable'",
        "HTTPStatusError: 500 Internal Server Error for url",
        "urlscan rate limit (429 too many requests)",
        "ReadTimeout: the operation timed out",
        "ConnectionResetError: connection reset by peer",
        "httpx.ConnectError: connection refused",
        "IncompleteRead: chunked read incomplete",
        "simulated 503 Service Unavailable (fault injection)",
    ]:
        assert _http.is_transient_error(msg) is True, msg


def test_deterministic_cases_not_retried():
    for msg in [
        "HTTPStatusError: Client error '404 Not Found'",
        "HTTPStatusError: Client error '403 Forbidden'",
        "invalid domain: 'bad!'",
        "refusing to fetch a non-public host: 127.0.0.1",
        "NXDOMAIN: the domain does not resolve",
        "HTTPStatusError: Client error '422 Unprocessable Entity'",
    ]:
        assert _http.is_transient_error(msg) is False, msg


def test_empty_and_none():
    assert _http.is_transient_error("") is False
    assert _http.is_transient_error(None) is False
