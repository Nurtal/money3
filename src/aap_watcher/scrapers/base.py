"""Polite crawler base.

Scraping ethics are a hard project constraint (README: scraping ethics):
respect robots.txt, rate-limit, cache downloads, descriptive User-Agent, never
bypass auth. This base handles those concerns so source adapters focus on
parsing.
"""

from __future__ import annotations

import os
import re
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import httpx

from ..extraction.base import Document

_USER_AGENT = "AAPWatcher/0.1 (+https://example.org/aap-watcher; polite crawler)"
_TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r'href="(?P<url>https?://[^"]+)"', re.IGNORECASE)


class BaseScraper(ABC):
    """Base class for all source adapters."""

    source_name: str = "base"
    requests_per_second: float = 0.5
    respect_robots_txt: bool = True

    def __init__(self, cache_dir: str = "data/raw", timeout: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=timeout, headers={"User-Agent": _USER_AGENT}
        )

    # --- polite utilities -------------------------------------------------

    def _robots_allows(self, url: str) -> bool:
        if not self.respect_robots_txt:
            return True
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            with urlopen(robots_url, timeout=self.timeout) as resp:  # noqa: S310
                rp = __import__("urllib.robotparser", fromlist=["RobotFileParser"]).RobotFileParser()
                rp.parse(resp.read().decode().splitlines())
                return rp.can_fetch(_USER_AGENT, url)
        except Exception:
            # When robots.txt is unreachable, be conservative: skip live fetch.
            return False

    def _rate_limit(self) -> None:
        if self.requests_per_second > 0:
            time.sleep(1.0 / self.requests_per_second)

    @staticmethod
    def html_to_text(html: str) -> str:
        text = _TAG_RE.sub(" ", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"\s+", " ", text)
        try:
            from html import unescape

            text = unescape(text)
        except Exception:
            pass
        return text.strip()

    # --- public API -------------------------------------------------------

    def fetch(self, url: str, html: Optional[str] = None) -> str:
        """Return HTML for ``url``, using ``html`` directly if provided (offline)."""
        if html is not None:
            return html
        if not self._robots_allows(url):
            raise PermissionError(f"robots.txt disallows: {url}")
        self._rate_limit()
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.text

    @abstractmethod
    def discover(self, html: Optional[str] = None) -> Iterator[Document]:
        """Yield normalised Documents for this source."""
        ...

    def close(self) -> None:
        self._client.close()
