import json
import os
import time
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen

import pytest

APP_BASE_URL_ENV = "APP_BASE_URL"
STARTUP_TIMEOUT_SECONDS = 120
RETRY_INTERVAL_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 5
HTTP_OK = 200
HTTP_FOUND = 302


def _request(base_url: str, path: str) -> tuple[int, str]:
    request = Request(f"{base_url}{path}", method="GET")  # noqa: S310
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # noqa: S310
            body = response.read().decode("utf-8", errors="replace")
            return response.getcode(), body
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body


@pytest.fixture(scope="session")
def app_base_url() -> str:
    value = os.getenv(APP_BASE_URL_ENV)
    if not value:
        pytest.fail(f"{APP_BASE_URL_ENV} is not set")

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        pytest.fail(
            f"{APP_BASE_URL_ENV} must be an absolute HTTP(S) URL, got: {value}",
        )

    return value.rstrip("/")


@pytest.fixture(scope="session")
def app_is_ready(app_base_url: str) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    last_error = "no response"

    while time.monotonic() < deadline:
        try:
            status, body = _request(app_base_url, "/health")
        except URLError as exc:
            last_error = f"connection error: {exc}"
        else:
            if status == HTTP_OK:
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError as exc:
                    last_error = (
                        f"invalid JSON in /health response: {exc}; body={body!r}"
                    )
                else:
                    if payload == {"status": "ok"}:
                        return
                    last_error = f"unexpected /health payload: {payload!r}"
            else:
                last_error = f"unexpected /health status: {status}; body={body!r}"

        time.sleep(RETRY_INTERVAL_SECONDS)

    pytest.fail(
        "Container app did not become healthy in time. "
        f"Timeout: {STARTUP_TIMEOUT_SECONDS}s; last error: {last_error}",
    )


def test_health_endpoint_from_built_image(
    app_base_url: str,
    app_is_ready: None,
) -> None:
    status, body = _request(app_base_url, "/health")

    assert status == HTTP_OK
    assert json.loads(body) == {"status": "ok"}


def test_homepage_from_built_image(app_base_url: str, app_is_ready: None) -> None:
    status, _ = _request(app_base_url, "/")

    assert status in {HTTP_OK, HTTP_FOUND}
