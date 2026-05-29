from __future__ import annotations
import json
import random
import urllib.parse
import urllib.request

_BASE = "https://api.giphy.com/v1/gifs"


def _default_fetch_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gif_url(gif: dict) -> str | None:
    return (gif or {}).get("images", {}).get("original", {}).get("url") or None


class GiphyClient:
    """Search GIPHY for GIF URLs. `fetch_json` is injectable for tests."""

    def __init__(self, api_key: str, fetch_json=_default_fetch_json):
        self._api_key = api_key
        self._fetch = fetch_json

    def search(self, term: str, count: int = 3) -> list[str]:
        """Return up to `count` random, distinct GIF URLs from the top results.
        Empty list if nothing matched. Draws from a narrow top pool for relevance."""
        data = self._fetch(f"{_BASE}/search", {
            "api_key": self._api_key,
            "q": term,
            "limit": 15,
            "rating": "pg-13",
        })
        results = (data or {}).get("data") or []
        urls = [u for u in (_gif_url(g) for g in results) if u]
        if not urls:
            return []
        return random.sample(urls, min(count, len(urls)))

    def random_meme(self) -> str | None:
        data = self._fetch(f"{_BASE}/random", {
            "api_key": self._api_key,
            "tag": "meme",
            "rating": "pg-13",
        })
        return _gif_url((data or {}).get("data") or {})
