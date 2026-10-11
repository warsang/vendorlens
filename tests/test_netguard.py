"""Network guard: strict host validation against SSRF-style inputs (P0.4)."""
import pytest

from vendorlens.tools import _netguard as ng


@pytest.mark.parametrize("value", [
    "acme.com", "stripe.com", "sub.acme.com", "ACME.COM",
    "xn--strae-oqa.example", "acme.com.",
])
def test_accepts_real_domains(value):
    assert ng.normalize_domain(value) is not None


@pytest.mark.parametrize("value", [
    "localhost", "127.0.0.1", "10.0.0.5", "192.168.1.1",
    "169.254.169.254", "0.0.0.0", "2130706433",
    "acme.com/", "acme.com:8080", "user@acme.com", "https://acme.com/",
    "acme.com?q=1", "acme.com#frag", "acme", "acme.123", "a b.com",
    "a..b.com", "-acme.com", "acme-.com", "../etc/passwd", "",
    "acme\\evil.com", "ftp://acme.com",
])
def test_rejects_hostile_inputs(value):
    assert ng.normalize_domain(value) is None


def test_rejects_internal_ips():
    for ip in ("127.0.0.1", "169.254.169.254", "10.0.0.1"):
        assert ng.host_is_public(ip) is False


def test_public_host_resolves_public():
    # dns.google resolves to public addresses only.
    assert ng.host_is_public("dns.google") is True


def test_host_from_url():
    assert ng.host_from_url("https://acme.com/path") == "acme.com"
    assert ng.host_from_url("http://sub.acme.com") == "sub.acme.com"
    assert ng.host_from_url("javascript:alert(1)") is None
    assert ng.host_from_url("127.0.0.1") is None
