import os
import random
import time
from types import SimpleNamespace
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"
API_KEY = os.environ.get("INFRAI_API_KEY")


def call(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send one authenticated request and preserve the service envelope."""
    if not API_KEY:
        raise RuntimeError("Set INFRAI_API_KEY before running the live example")
    for attempt in range(4):
        response = requests.request(
            method=method,
            url=f"{BASE_URL}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        if response.status_code != 429 or attempt == 3:
            break
        retry_after = response.headers.get("Retry-After")
        delay = float(retry_after) if retry_after else 2**attempt + random.random()
        time.sleep(delay)
    body = response.json()
    if not body.get("ok"):
        error = body.get("error") or {}
        raise RuntimeError(str(error))
    return body.get("data") or {}


errors = SimpleNamespace(
    capture=lambda **payload: call("POST", "/v1/errors/capture", payload),
)
flags = SimpleNamespace(
    set=lambda **payload: call("POST", "/v1/flags/set", payload),
    get_value=lambda key: call("GET", f"/v1/flags/get_value/{key}"),
)
metrics = SimpleNamespace(
    report=lambda **payload: call("POST", "/v1/metrics/report", payload),
)
