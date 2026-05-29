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
    """Search GIPHY and return a single GIF URL. `fetch_json` is injectable for tests."""

    def __init__(self, api_key: str, fetch_json=_default_fetch_json):
        self._api_key = api_key
        self._fetch = fetch_json

    def search(self, term: str) -> str | None:
        data = self._fetch(f"{_BASE}/search", {
            "api_key": self._api_key,
            "q": term,
            "limit": 25,
            "rating": "pg-13",
        })
        results = (data or {}).get("data") or []
        if not results:
            return None
        return _gif_url(random.choice(results))

    def random_meme(self) -> str | None:
        data = self._fetch(f"{_BASE}/random", {
            "api_key": self._api_key,
            "tag": "meme",
            "rating": "pg-13",
        })
        return _gif_url((data or {}).get("data") or {})
