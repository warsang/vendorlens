"""Crustdata tool: unmatched domains are a no-record answer, not a failure.

Covers the 400-on-unmatchable-domain path (reserved TLDs such as .example),
the happy path, and the rule that real errors stay failures.
"""
import asyncio

import httpx

from vendorlens.tools import crustdata


class _Resp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Client error '{self.status_code}'",
                request=httpx.Request("POST", "https://api.crustdata.example"),
                response=httpx.Response(self.status_code))

    def json(self):
        return self._payload


class _Client:
    """Minimal async-context-manager stand-in for httpx.AsyncClient."""

    def __init__(self, status=200, payload=None, exc=None):
        self._status = status
        self._payload = payload if payload is not None else []
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, *args, **kwargs):
        if self._exc:
            raise self._exc
        return _Resp(self._status, self._payload)


def _run(monkeypatch, client):
    monkeypatch.setenv("CRUSTDATA_API_KEY", "test-key")
    monkeypatch.setattr(crustdata.httpx, "AsyncClient",
                        lambda **kwargs: client)
    return asyncio.run(crustdata.run({"domain": "acme-cloud-services.example"},
                                     {}))


def test_unmatchable_domain_is_no_record(monkeypatch):
    # Crustdata answers 400 for domains it cannot match (e.g. .example):
    # the agent must read that as "no business record", not a broken tool.
    res = _run(monkeypatch, _Client(status=400))
    assert res["ok"] is True
    assert res["data"]["found"] is False
    assert res["sources"]


def test_match_is_parsed(monkeypatch):
    payload = [{"matches": [{
        "confidence_score": 92,
        "company_data": {
            "basic_info": {"name": "Acme Cloud Services Ltd",
                           "employee_count_range": "51-200",
                           "year_founded": 2019},
            "locations": {"headquarters": "Berlin, Germany"},
        },
    }]}]
    res = _run(monkeypatch, _Client(status=200, payload=payload))
    assert res["ok"] is True
    assert res["data"]["found"] is True
    assert res["data"]["company_name"] == "Acme Cloud Services Ltd"
    assert res["data"]["headcount"] == "51-200"


def test_network_error_still_fails(monkeypatch):
    res = _run(monkeypatch,
               _Client(exc=httpx.ConnectError("connection refused")))
    assert res["ok"] is False
    assert "ConnectError" in res["error"]


def test_missing_key_still_fails(monkeypatch):
    monkeypatch.delenv("CRUSTDATA_API_KEY", raising=False)
    res = asyncio.run(crustdata.run({"domain": "acme.com"}, {}))
    assert res["ok"] is False
    assert "CRUSTDATA_API_KEY" in res["error"]
