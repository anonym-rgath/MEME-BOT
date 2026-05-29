# GIPHY Part A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/gif <term>` and `/meme` commands that fetch a GIF from GIPHY and send it to the chat.

**Architecture:** A pure `GiphyClient` (HTTP via an injectable `fetch_json`, so tests need no network) exposes `search(term)` and `random_meme()`. The bot gets two new command handlers that call the client off the event loop and `send_animation` the resulting URL. If no API key is configured, the commands reply with a friendly notice. Buttons/other features are untouched.

**Tech Stack:** Python 3.11, python-telegram-bot 21.6, stdlib `urllib` (no new dependency), pytest.

---

## File Structure

```
src/memebot/
├── config.py            # MODIFY: add giphy_api_key
├── giphy/
│   ├── __init__.py      # NEW (empty)
│   └── client.py        # NEW: GiphyClient.search / random_meme (pure, injectable fetch)
└── bot/
    ├── handlers.py      # MODIFY: giphy dep + on_gif/on_meme + HELP_TEXT
    └── app.py           # MODIFY: build GiphyClient (or None), register /gif /meme
tests/
└── test_giphy.py        # NEW: GiphyClient with a fake fetch_json
```

---

## Task GA1: Config — GIPHY API key

**Files:**
- Modify: `src/memebot/config.py`, `.env.example`
- Test: `tests/test_config.py`

- [ ] **Step 1: Add a failing test** — append to `tests/test_config.py`:

```python
def test_giphy_key_default_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    assert Settings.from_env(base).giphy_api_key == ""
    s = Settings.from_env({**base, "GIPHY_API_KEY": "gk"})
    assert s.giphy_api_key == "gk"
```

- [ ] **Step 2: Run, expect FAIL**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_config.py::test_giphy_key_default_and_override -v`
Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'giphy_api_key'`

- [ ] **Step 3: Implement.** In `src/memebot/config.py`, add a field to the `Settings` dataclass after `data_dir`:

```python
    giphy_api_key: str = ""
```

And in `from_env`'s `return cls(...)`, add after the `data_dir=...` line:

```python
            giphy_api_key=env.get("GIPHY_API_KEY", cls.giphy_api_key),
```

- [ ] **Step 4: Run, expect PASS**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_config.py -v`
Expected: all config tests PASS.

- [ ] **Step 5: Update `.env.example`** — add after the `DATA_DIR=...` line:

```
# Free GIPHY API key from developers.giphy.com (optional; enables /gif and /meme)
GIPHY_API_KEY=
```

- [ ] **Step 6: Commit**

```bash
git add src/memebot/config.py tests/test_config.py .env.example
git commit -m "feat: config for GIPHY API key"
```

---

## Task GA2: GiphyClient

**Files:**
- Create: `src/memebot/giphy/__init__.py` (empty), `src/memebot/giphy/client.py`
- Test: `tests/test_giphy.py`

- [ ] **Step 1: Write the failing test** — `tests/test_giphy.py`:

```python
from memebot.giphy.client import GiphyClient

class FakeFetch:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def __call__(self, url, params):
        self.calls.append((url, params))
        return self.response

def test_search_returns_url_with_pg13_and_key():
    fake = FakeFetch({"data": [{"images": {"original": {"url": "https://x.gif"}}}]})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.search("cats") == "https://x.gif"
    url, params = fake.calls[0]
    assert "search" in url
    assert params["q"] == "cats"
    assert params["rating"] == "pg-13"
    assert params["api_key"] == "K"

def test_search_empty_returns_none():
    fake = FakeFetch({"data": []})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.search("nope") is None

def test_random_meme_returns_url():
    fake = FakeFetch({"data": {"images": {"original": {"url": "https://r.gif"}}}})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.random_meme() == "https://r.gif"
    url, params = fake.calls[0]
    assert "random" in url
    assert params["tag"] == "meme"
    assert params["rating"] == "pg-13"

def test_random_meme_empty_returns_none():
    fake = FakeFetch({"data": {}})
    c = GiphyClient(api_key="K", fetch_json=fake)
    assert c.random_meme() is None
```

- [ ] **Step 2: Run, expect FAIL**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_giphy.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'memebot.giphy.client'`

- [ ] **Step 3: Implement.** `src/memebot/giphy/__init__.py` is empty. `src/memebot/giphy/client.py`:

```python
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
```

- [ ] **Step 4: Run, expect PASS** (4 tests)

Run: `PYTHONPATH=src venv/bin/pytest tests/test_giphy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memebot/giphy/ tests/test_giphy.py
git commit -m "feat: GiphyClient with search + random_meme (injectable fetch)"
```

---

## Task GA3: Wire /gif and /meme into the bot

**Files:**
- Modify: `src/memebot/bot/handlers.py`, `src/memebot/bot/app.py`, `README.md`

No unit tests (Telegram-coupled); verify with the import check + full suite.

- [ ] **Step 1: Add the giphy dependency to `Handlers`** — in `src/memebot/bot/handlers.py`, add the import near the other imports:

```python
from memebot.giphy.client import GiphyClient
```

Change the constructor to accept `giphy`. From:

```python
    def __init__(
        self,
        settings: Settings,
        faces: FaceLibrary,
        swapper: FaceSwapProvider,
        text_remover: TextRemovalProvider,
        store: SessionStore | None = None,
    ):
        self.s = settings
        self.faces = faces
        self.swapper = swapper
        self.text_remover = text_remover
        self.store = store or SessionStore()
```

to:

```python
    def __init__(
        self,
        settings: Settings,
        faces: FaceLibrary,
        swapper: FaceSwapProvider,
        text_remover: TextRemovalProvider,
        giphy: GiphyClient | None = None,
        store: SessionStore | None = None,
    ):
        self.s = settings
        self.faces = faces
        self.swapper = swapper
        self.text_remover = text_remover
        self.giphy = giphy
        self.store = store or SessionStore()
```

- [ ] **Step 2: Extend `HELP_TEXT`** — change the existing `HELP_TEXT` constant to add two lines before the closing paragraph:

```python
HELP_TEXT = (
    "🤖 Du kannst Buttons nutzen oder Befehle:\n"
    "• /text Oben | Unten — Text aufs Bild/Video\n"
    "• /face <Name> — Gesicht tauschen (Bild)\n"
    "• /clean — Text entfernen (Bild)\n"
    "• /recaption Oben | Unten — säubern + neu betexten (Bild)\n"
    "• /gif <Begriff> — GIF von GIPHY suchen\n"
    "• /meme — zufälliges Meme-GIF\n\n"
    "Schick den Befehl als Bildunterschrift mit, oder als Nachricht zum "
    "zuletzt gesendeten Bild."
)
```

- [ ] **Step 3: Add the `on_gif` and `on_meme` handlers** — add these methods to the `Handlers` class (e.g. after `on_command`):

```python
    async def on_gif(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        msg = update.message
        if self.giphy is None:
            return await msg.reply_text("🎬 GIPHY ist nicht konfiguriert (API-Key fehlt).")
        parts = msg.text.split(maxsplit=1)
        term = parts[1].strip() if len(parts) > 1 else ""
        if not term:
            return await msg.reply_text("Usage: /gif <Begriff>")
        try:
            url = await asyncio.to_thread(self.giphy.search, term)
        except Exception:
            url = None
        if not url:
            return await msg.reply_text("🤷 Nichts gefunden, versuch's anders.")
        await ctx.bot.send_animation(msg.chat_id, animation=url)

    async def on_meme(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        msg = update.message
        if self.giphy is None:
            return await msg.reply_text("🎬 GIPHY ist nicht konfiguriert (API-Key fehlt).")
        try:
            url = await asyncio.to_thread(self.giphy.random_meme)
        except Exception:
            url = None
        if not url:
            return await msg.reply_text("🤷 Gerade kein Meme bekommen, versuch's nochmal.")
        await ctx.bot.send_animation(msg.chat_id, animation=url)
```

- [ ] **Step 4: Wire it in `app.py`** — in `src/memebot/bot/app.py`, add the import and build the client. Add near the other imports:

```python
from memebot.giphy.client import GiphyClient
```

Inside `build_application`, after the `text_remover = ...` block and before `handlers = Handlers(...)`, add:

```python
    giphy = GiphyClient(settings.giphy_api_key) if settings.giphy_api_key else None
```

Change the `Handlers(...)` call to pass it:

```python
    handlers = Handlers(
        settings=settings,
        faces=FaceLibrary(settings.data_dir),
        swapper=swapper,
        text_remover=text_remover,
        giphy=giphy,
    )
```

Register the two command handlers — change the command-handler block to add `gif` and `meme`:

```python
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help))
    app.add_handler(CommandHandler("skip", handlers.on_text))
    app.add_handler(CommandHandler(["text", "face", "clean", "recaption"], handlers.on_command))
    app.add_handler(CommandHandler("gif", handlers.on_gif))
    app.add_handler(CommandHandler("meme", handlers.on_meme))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handlers.on_media))
    app.add_handler(CallbackQueryHandler(handlers.on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))
    return app
```

- [ ] **Step 5: Update `README.md`** — in the `## Commands` list, add:

```markdown
- `/gif <term>` — search a GIF on GIPHY
- `/meme` — random meme GIF
```

- [ ] **Step 6: Import + full-suite check**

Run: `PYTHONPATH=src venv/bin/python -c "import memebot.main; import memebot.bot.handlers; import memebot.bot.app; print('ok')"`
Expected: prints `ok`

Run: `PYTHONPATH=src venv/bin/pytest -q`
Expected: all tests pass (incl. new GiphyClient tests).

- [ ] **Step 7: Commit**

```bash
git add src/memebot/bot/handlers.py src/memebot/bot/app.py README.md
git commit -m "feat: /gif and /meme commands (GIPHY search & send)"
```

---

## Task GA4: E2E verification (needs a GIPHY key)

**Prerequisite:** free `GIPHY_API_KEY` from developers.giphy.com in the Pi `.env`.

- [ ] **Step 1:** `PYTHONPATH=src venv/bin/pytest -q` → all green.
- [ ] **Step 2:** Deploy: `git pull && ./scripts/start.sh && ./scripts/logs.sh`.
- [ ] **Step 3:** `/gif katze` → a cat GIF arrives; repeat → ideally a different one.
- [ ] **Step 4:** `/meme` → a random meme GIF.
- [ ] **Step 5:** `/gif` with no term → usage message.
- [ ] **Step 6:** (Temporarily) blank `GIPHY_API_KEY` + restart → `/gif x` replies "nicht konfiguriert". Restore the key afterward.

---

## Self-Review notes

- **Spec coverage:** `/gif <term>` random-from-top (GA2 `search` + GA3 `on_gif`) ✓; `/meme` random (GA2 `random_meme` + GA3 `on_meme`) ✓; pg-13 rating (GA2) ✓; key-missing notice (GA3 `giphy is None`) ✓; config key (GA1) ✓; off-event-loop via `asyncio.to_thread` (GA3) ✓; pure client unit-tested with fake fetch, handlers E2E (GA2, GA4) ✓; buttons/other features untouched ✓.
- **Placeholder scan:** none — all code complete.
- **Type consistency:** `GiphyClient(api_key, fetch_json)`, `.search(term) -> str | None`, `.random_meme() -> str | None`; `Handlers(..., giphy: GiphyClient | None = None, store=...)` — note `giphy` is added BEFORE `store` so existing positional callers/tests that omit both still work, and `app.py` passes `giphy=` by keyword. `on_gif`/`on_meme` use `asyncio` and `Update`/`ContextTypes` already imported in handlers.py.
- **Dependency note:** `asyncio` is already imported in handlers.py (used by the pipeline); no new import needed there beyond `GiphyClient`.
```
