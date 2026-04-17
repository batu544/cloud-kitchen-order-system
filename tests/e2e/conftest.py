"""
Shared Playwright fixtures and session setup for E2E tests.
"""
import pytest
import urllib.request

BASE = "http://localhost:5001"


@pytest.fixture(scope="session", autouse=True)
def reset_rate_limits():
    """Reset Flask-Limiter counters before the test session to prevent
    rate limit bleed-over between consecutive test runs."""
    try:
        req = urllib.request.Request(
            f"{BASE}/debug/reset-limits", method="POST",
            headers={"Content-Length": "0"}
        )
        urllib.request.urlopen(req, data=b"", timeout=3)
    except Exception:
        pass  # Endpoint only exists in DEBUG mode; silently skip otherwise
