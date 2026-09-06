from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import httpx

USER_AGENT = "ironman-pro-standings/0.1 (personal project)"
CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache"
MIN_INTERVAL = 1.0


class Fetcher:
    """httpx client wrapper that rate-limits GETs to <=1/sec and optionally
    caches responses under backend/.cache/ when IPS_CACHE=1."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        )
        self._last_ts = 0.0
        self._cache = os.environ.get("IPS_CACHE") == "1"

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode()).hexdigest()
        return CACHE_DIR / f"{digest}.html"

    def get(self, url: str) -> str:
        if self._cache:
            path = self._cache_path(url)
            if path.exists():
                return path.read_text(encoding="utf-8")

        wait = MIN_INTERVAL - (time.monotonic() - self._last_ts)
        if wait > 0:
            time.sleep(wait)
        resp = self._client.get(url)
        self._last_ts = time.monotonic()
        resp.raise_for_status()
        html = resp.text

        if self._cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self._cache_path(url).write_text(html, encoding="utf-8")
        return html

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Fetcher":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
