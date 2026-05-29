# Text Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an AI text-removal capability to the Meme-Bot — a "🧹 Text entfernen" button (clean an image) and a "🆕 Vorlage neu betexten" button (clean, then add new meme text), images only in v1.

**Architecture:** A new `TextRemovalProvider` (Replicate, mirrors the existing face-swap provider) exposes `remove_text(image_path) -> url`. The bot gets two new actions (`clean`, `recaption`); the handler pipeline runs an optional text-removal stage first, then the existing optional text-overlay stage. Video is rejected for cloud edits in v1, consistent with face-swap.

**Tech Stack:** Python 3.11, python-telegram-bot 21.6, replicate, Pillow (existing), pytest. Default model `adirik/inst-inpaint` (text-guided removal: image + instruction).

---

## File Structure

```
src/memebot/
├── config.py                 # MODIFY: add text_removal_model + text_removal_prompt
├── replicate_io.py           # NEW: shared first_url(output) helper
├── faceswap/provider.py      # MODIFY: use shared first_url (DRY)
├── textremove/
│   ├── __init__.py           # NEW (empty)
│   └── provider.py           # NEW: TextRemovalProvider + ReplicateTextRemover
└── bot/
    ├── keyboards.py          # MODIFY: add clean + recaption buttons
    ├── handlers.py           # MODIFY: new actions, video guard, removal stage, ctor dep
    └── app.py                # MODIFY: build + inject ReplicateTextRemover
tests/
├── test_config.py            # MODIFY: assert new fields
├── test_replicate_io.py      # NEW: first_url
└── test_textremove.py        # NEW: provider with fake client
```

---

## Task 1: Config — text-removal model + instruction

**Files:**
- Modify: `src/memebot/config.py`
- Test: `tests/test_config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add a failing test** — append to `tests/test_config.py`:

```python
def test_text_removal_defaults_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    s = Settings.from_env(base)
    assert s.text_removal_model == "adirik/inst-inpaint"
    assert s.text_removal_prompt == "remove all the text"
    s2 = Settings.from_env({**base,
        "REPLICATE_TEXT_REMOVAL_MODEL": "owner/model",
        "TEXT_REMOVAL_PROMPT": "erase text"})
    assert s2.text_removal_model == "owner/model"
    assert s2.text_removal_prompt == "erase text"
```

- [ ] **Step 2: Run, expect FAIL**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_config.py::test_text_removal_defaults_and_override -v`
Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'text_removal_model'`

- [ ] **Step 3: Implement** — in `src/memebot/config.py`, add two fields to the `Settings` dataclass after `video_model`:

```python
    text_removal_model: str = "adirik/inst-inpaint"
    text_removal_prompt: str = "remove all the text"
```

And in `from_env`, add these two keyword args to the `cls(...)` call (after `video_model=...`):

```python
            text_removal_model=env.get("REPLICATE_TEXT_REMOVAL_MODEL", cls.text_removal_model),
            text_removal_prompt=env.get("TEXT_REMOVAL_PROMPT", cls.text_removal_prompt),
```

- [ ] **Step 4: Run, expect PASS** (and the whole config suite)

Run: `PYTHONPATH=src venv/bin/pytest tests/test_config.py -v`
Expected: PASS (all config tests)

- [ ] **Step 5: Update `.env.example`** — add after the `REPLICATE_VIDEO_MODEL=` line:

```
# Text-removal model (image + instruction). Verify slug/fields on replicate.com.
REPLICATE_TEXT_REMOVAL_MODEL=adirik/inst-inpaint
TEXT_REMOVAL_PROMPT=remove all the text
```

- [ ] **Step 6: Commit**

```bash
git add src/memebot/config.py tests/test_config.py .env.example
git commit -m "feat: config for text-removal model + instruction"
```

---

## Task 2: Shared `first_url` helper (DRY)

The face-swap provider has a private `_first_url`. Text-removal needs the same logic, so extract it to a shared module and have both use it.

**Files:**
- Create: `src/memebot/replicate_io.py`
- Modify: `src/memebot/faceswap/provider.py`
- Test: `tests/test_replicate_io.py`

- [ ] **Step 1: Write the failing test** — `tests/test_replicate_io.py`:

```python
from memebot.replicate_io import first_url

class _Obj:
    def __init__(self, url): self.url = url

def test_first_url_str():
    assert first_url("https://a") == "https://a"

def test_first_url_list_takes_first():
    assert first_url(["https://a", "https://b"]) == "https://a"

def test_first_url_object_with_url_attr():
    assert first_url(_Obj("https://x")) == "https://x"
```

- [ ] **Step 2: Run, expect FAIL**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_replicate_io.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'memebot.replicate_io'`

- [ ] **Step 3: Implement** — `src/memebot/replicate_io.py`:

```python
from __future__ import annotations


def first_url(output) -> str:
    """Normalize a Replicate result (str | list | file-like with .url) to one URL string."""
    if isinstance(output, list):
        output = output[0]
    if isinstance(output, str):
        return output
    return getattr(output, "url", str(output))
```

- [ ] **Step 4: Refactor `src/memebot/faceswap/provider.py`** — remove the local `_first_url` function entirely and import the shared one. Change the top of the file from:

```python
from __future__ import annotations
from typing import Protocol


class FaceSwapProvider(Protocol):
    def swap_image(self, target_path: str, face_path: str) -> str: ...
    def swap_video(self, target_path: str, face_path: str) -> str: ...


def _first_url(output) -> str:
    """Replicate returns a str, a list, or a file-like object with .url."""
    if isinstance(output, list):
        output = output[0]
    if isinstance(output, str):
        return output
    return getattr(output, "url", str(output))
```

to:

```python
from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class FaceSwapProvider(Protocol):
    def swap_image(self, target_path: str, face_path: str) -> str: ...
    def swap_video(self, target_path: str, face_path: str) -> str: ...
```

Then in `ReplicateProvider._run`, change the final line `return _first_url(output)` to `return first_url(output)`.

- [ ] **Step 5: Run both test files, expect PASS (no regression)**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_replicate_io.py tests/test_faceswap.py -v`
Expected: PASS (3 + 3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/memebot/replicate_io.py src/memebot/faceswap/provider.py tests/test_replicate_io.py
git commit -m "refactor: extract shared first_url helper for Replicate output"
```

---

## Task 3: TextRemovalProvider

**Files:**
- Create: `src/memebot/textremove/__init__.py` (empty), `src/memebot/textremove/provider.py`
- Test: `tests/test_textremove.py`

- [ ] **Step 1: Write the failing test** — `tests/test_textremove.py`:

```python
from memebot.textremove.provider import ReplicateTextRemover

class FakeReplicate:
    def __init__(self, output):
        self._output = output
        self.calls = []
    def run(self, model, input):
        self.calls.append((model, input))
        return self._output

def test_remove_text_passes_model_image_and_prompt(tmp_path):
    fake = FakeReplicate(output="https://result/clean.jpg")
    prov = ReplicateTextRemover(client=fake, model="owner/textrm", instruction="remove all the text")
    img = tmp_path / "in.jpg"; img.write_bytes(b"x")

    url = prov.remove_text(str(img))

    assert url == "https://result/clean.jpg"
    assert fake.calls[0][0] == "owner/textrm"
    assert fake.calls[0][1]["prompt"] == "remove all the text"
    assert "image" in fake.calls[0][1]

def test_remove_text_list_output_returns_first(tmp_path):
    fake = FakeReplicate(output=["https://a", "https://b"])
    prov = ReplicateTextRemover(client=fake, model="m", instruction="x")
    img = tmp_path / "in.jpg"; img.write_bytes(b"x")
    assert prov.remove_text(str(img)) == "https://a"
```

- [ ] **Step 2: Run, expect FAIL**

Run: `PYTHONPATH=src venv/bin/pytest tests/test_textremove.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'memebot.textremove.provider'`

- [ ] **Step 3: Implement.** `src/memebot/textremove/__init__.py` is empty. `src/memebot/textremove/provider.py`:

```python
from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class TextRemovalProvider(Protocol):
    def remove_text(self, image_path: str) -> str: ...


class ReplicateTextRemover:
    """Remove text from an image via a text-guided Replicate model.

    NOTE: input keys (`image` / `prompt`) depend on the chosen model. Verify the
    current model's schema on replicate.com and adjust the `input={...}` dict if needed.
    """

    def __init__(self, client, model: str, instruction: str):
        self._client = client
        self._model = model
        self._instruction = instruction

    def remove_text(self, image_path: str) -> str:
        with open(image_path, "rb") as image:
            output = self._client.run(
                self._model,
                input={"image": image, "prompt": self._instruction},
            )
        return first_url(output)
```

- [ ] **Step 4: Run, expect PASS** (2 tests)

Run: `PYTHONPATH=src venv/bin/pytest tests/test_textremove.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/memebot/textremove/ tests/test_textremove.py
git commit -m "feat: Replicate text-removal provider behind abstraction"
```

---

## Task 4: Keyboards — two new buttons

**Files:**
- Modify: `src/memebot/bot/keyboards.py`

- [ ] **Step 1: Edit `action_keyboard`** — change it from:

```python
def action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text hinzufügen", callback_data="action:text")],
        [InlineKeyboardButton("🔁 Gesicht tauschen", callback_data="action:face")],
        [InlineKeyboardButton("✨ Beides", callback_data="action:both")],
        [InlineKeyboardButton("❌ Abbrechen", callback_data="action:cancel")],
    ])
```

to:

```python
def action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text hinzufügen", callback_data="action:text")],
        [InlineKeyboardButton("🔁 Gesicht tauschen", callback_data="action:face")],
        [InlineKeyboardButton("✨ Beides", callback_data="action:both")],
        [InlineKeyboardButton("🧹 Text entfernen", callback_data="action:clean")],
        [InlineKeyboardButton("🆕 Vorlage neu betexten", callback_data="action:recaption")],
        [InlineKeyboardButton("❌ Abbrechen", callback_data="action:cancel")],
    ])
```

- [ ] **Step 2: Import check**

Run: `PYTHONPATH=src venv/bin/python -c "from memebot.bot.keyboards import action_keyboard; action_keyboard(); print('ok')"`
Expected: prints `ok`

- [ ] **Step 3: Commit**

```bash
git add src/memebot/bot/keyboards.py
git commit -m "feat: add text-removal buttons to action keyboard"
```

---

## Task 5: Handlers + app wiring

**Files:**
- Modify: `src/memebot/bot/handlers.py`
- Modify: `src/memebot/bot/app.py`

- [ ] **Step 1: Add the provider dependency to `Handlers`** — in `src/memebot/bot/handlers.py`, change the constructor from:

```python
    def __init__(
        self,
        settings: Settings,
        faces: FaceLibrary,
        swapper: FaceSwapProvider,
        store: SessionStore | None = None,
    ):
        self.s = settings
        self.faces = faces
        self.swapper = swapper
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
        store: SessionStore | None = None,
    ):
        self.s = settings
        self.faces = faces
        self.swapper = swapper
        self.text_remover = text_remover
        self.store = store or SessionStore()
```

And add the import near the other provider import:

```python
from memebot.textremove.provider import TextRemovalProvider
```

- [ ] **Step 2: Extend the action routing in `on_button`** — change the `if data.startswith("action:"):` block from:

```python
        if data.startswith("action:"):
            sess.action = data.split(":", 1)[1]
            # v1: video face swap is deferred — videos support text only.
            if sess.is_video and sess.action in ("face", "both"):
                self._discard_session_media(sess)
                self.store.clear(chat_id)
                return await q.edit_message_text(
                    "🔁 Gesichtstausch für Videos kommt später. "
                    "Bei Videos geht aktuell nur Text — schick ein Bild für "
                    "den Gesichtstausch.")
            if sess.action in ("text", "both"):
                sess.awaiting = "top_text"
                return await q.edit_message_text(
                    "Text oben? (oder /skip für keinen)")
            else:  # face only
                return await self._prompt_faces(q, sess)
```

to:

```python
        if data.startswith("action:"):
            sess.action = data.split(":", 1)[1]
            # v1: cloud edits (face swap, text removal) are image-only.
            if sess.is_video and sess.action in ("face", "both", "clean", "recaption"):
                self._discard_session_media(sess)
                self.store.clear(chat_id)
                return await q.edit_message_text(
                    "🪄 Cloud-Bearbeitung (Gesicht tauschen / Text entfernen) für "
                    "Videos kommt später. Bei Videos geht aktuell nur Text "
                    "hinzufügen — schick ein Bild für die anderen Funktionen.")
            if sess.action in ("text", "both", "recaption"):
                sess.awaiting = "top_text"
                return await q.edit_message_text(
                    "Text oben? (oder /skip für keinen)")
            if sess.action == "clean":
                return await self._run_pipeline(q, sess, ctx)
            # face only
            return await self._prompt_faces(q, sess)
```

- [ ] **Step 3: Add the text-removal stage to `_process_and_send`** — insert a new stage as the FIRST step inside the `try:` block, right after `current = sess.media_path`. Change:

```python
        try:
            current = sess.media_path
            # 1) face swap (cloud) if requested — images only in v1
            if sess.action in ("face", "both") and sess.chosen_face:
```

to:

```python
        try:
            current = sess.media_path
            # 1) text removal (cloud) if requested — images only in v1
            if sess.action in ("clean", "recaption"):
                removed = await asyncio.to_thread(self.text_remover.remove_text, current)
                local = self._tmp(".jpg")
                temp_files.append(local)
                await asyncio.to_thread(urllib.request.urlretrieve, removed, local)
                current = local
            # 2) face swap (cloud) if requested — images only in v1
            if sess.action in ("face", "both") and sess.chosen_face:
```

- [ ] **Step 4: Include `recaption` in the text-overlay stage** — change:

```python
            # 2) text overlay (local) if requested
            if sess.action in ("text", "both") and (sess.top_text or sess.bottom_text):
```

to:

```python
            # 3) text overlay (local) if requested
            if sess.action in ("text", "both", "recaption") and (sess.top_text or sess.bottom_text):
```

- [ ] **Step 5: Update `app.py` wiring** — in `src/memebot/bot/app.py`, change the imports/build. From:

```python
from memebot.faceswap.provider import ReplicateProvider
from memebot.bot.handlers import Handlers


def build_application(settings: Settings) -> Application:
    client = replicate.Client(api_token=settings.replicate_api_token)
    swapper = ReplicateProvider(
        client=client,
        image_model=settings.image_model,
        video_model=settings.video_model,
    )
    handlers = Handlers(
        settings=settings,
        faces=FaceLibrary(settings.data_dir),
        swapper=swapper,
    )
```

to:

```python
from memebot.faceswap.provider import ReplicateProvider
from memebot.textremove.provider import ReplicateTextRemover
from memebot.bot.handlers import Handlers


def build_application(settings: Settings) -> Application:
    client = replicate.Client(api_token=settings.replicate_api_token)
    swapper = ReplicateProvider(
        client=client,
        image_model=settings.image_model,
        video_model=settings.video_model,
    )
    text_remover = ReplicateTextRemover(
        client=client,
        model=settings.text_removal_model,
        instruction=settings.text_removal_prompt,
    )
    handlers = Handlers(
        settings=settings,
        faces=FaceLibrary(settings.data_dir),
        swapper=swapper,
        text_remover=text_remover,
    )
```

- [ ] **Step 6: Import + full-suite check**

Run: `PYTHONPATH=src venv/bin/python -c "import memebot.main; import memebot.bot.handlers; import memebot.bot.app; print('ok')"`
Expected: prints `ok`

Run: `PYTHONPATH=src venv/bin/pytest -q`
Expected: all tests pass (config + replicate_io + textremove + faceswap + renderer + faces + state)

- [ ] **Step 7: Commit**

```bash
git add src/memebot/bot/handlers.py src/memebot/bot/app.py
git commit -m "feat: wire text-removal actions (clean + recaption) into the bot flow"
```

---

## Task 6: Model verification + E2E (needs real token, deploy on Pi)

**Prerequisite:** real `REPLICATE_API_TOKEN` + Replicate billing active.

- [ ] **Step 1: Verify the model schema** — on replicate.com, open `adirik/inst-inpaint` (or chosen `REPLICATE_TEXT_REMOVAL_MODEL`). Confirm the input field names are `image` and `prompt`. If they differ (e.g. `instruction` instead of `prompt`, or a required mask), adjust the single `input={...}` dict in `src/memebot/textremove/provider.py` accordingly and re-run `tests/test_textremove.py` (update the asserted keys to match).

- [ ] **Step 2: Full unit suite green**

Run: `PYTHONPATH=src venv/bin/pytest -q`
Expected: all pass.

- [ ] **Step 3: Deploy on the Pi**

```bash
git pull && ./scripts/start.sh && ./scripts/logs.sh
```

- [ ] **Step 4: E2E — clean.** Send an image with baked-in text → tap **🧹 Text entfernen** → expect the text removed in the returned image.

- [ ] **Step 5: E2E — recaption.** Send an image with text → tap **🆕 Vorlage neu betexten** → enter top/bottom text → expect old text removed AND new meme text overlaid.

- [ ] **Step 6: E2E — video rejection.** Send a video → tap **🧹 Text entfernen** → expect the friendly "kommt später" message, no Replicate call.

- [ ] **Step 7: E2E — temp cleanup.** Inspect `DATA_DIR`: only `faces/<user_id>/*.jpg` remain; no stray temp files.

---

## Self-Review notes

- **Spec coverage:** clean action (Tasks 4,5) ✓; recaption action = remove + overlay (Tasks 4,5) ✓; images-only with video rejection (Task 5 Step 2) ✓; provider behind `remove_text()` interface hiding model choice (Task 3) ✓; config-driven model + instruction (Task 1) ✓; DRY `first_url` shared (Task 2) ✓; temp cleanup uses existing `_process_and_send` finally + `temp_files` tracking (Task 5) ✓; provider unit-tested with mock, handlers E2E (Tasks 3,6) ✓; #2 "undo own text" intentionally not built (YAGNI).
- **External-fact caveat (not a placeholder):** the model slug + its input keys (`image`/`prompt`) are external and verified in Task 6 Step 1; isolated to `.env` + one dict in `textremove/provider.py`.
- **Type consistency:** `remove_text(image_path) -> str`, `ReplicateTextRemover(client, model, instruction)`, actions `clean`/`recaption`, and the `Handlers(..., text_remover=...)` arg are used consistently across Tasks 3, 5, and app.py.
- **Pipeline order:** text-removal (stage 1) → face-swap (stage 2) → text-overlay (stage 3). For `recaption`, stage 1 + stage 3 run; for `clean`, only stage 1.
```
