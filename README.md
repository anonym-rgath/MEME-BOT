# MEME-BOT

A private Telegram bot for making memes: add text to images/videos/GIFs, swap faces,
remove text, and search GIFs — driven by inline buttons or commands. Long-polling, runs
as a Docker container (e.g. on a Raspberry Pi). Heavy AI work is offloaded to Replicate;
text overlay runs locally.

## Features
- ✏️ **Text** on images, videos and GIFs (local — Pillow + ffmpeg)
- 🔁 **Face swap** on images (generative editor, default `google/nano-banana`)
- 🧹 **Text removal** / template cleanup on images (default `black-forest-labs/flux-kontext-pro`)
- 🆕 **Recaption**: remove text, then add new text
- 🎬 **GIF search** (`/gif`, `/meme`) via GIPHY — and captioning GIFs
- 🧽 **`/clearchat`** to tidy the conversation
- 🔒 Whitelist (only allowed Telegram user IDs); per-user face library
- Buttons **and** commands (as an image caption or a follow-up message)

## Setup
1. @BotFather → `/newbot` → copy the bot token.
2. Your numeric Telegram user ID (e.g. via @userinfobot).
3. Replicate account + API token (replicate.com/account) with credit/billing.
4. *(optional)* free GIPHY API key (developers.giphy.com → **API**) for `/gif` and `/meme`.
5. `cp .env.example .env` and fill it in.

### Environment (`.env`)
**Required**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USERS` — comma-separated numeric user IDs
- `REPLICATE_API_TOKEN`

**Optional** (sensible defaults in code; model slugs + input field names are configurable so
you can swap models without code changes)
- `GIPHY_API_KEY` — enables `/gif` + `/meme` · `GIPHY_RESULT_COUNT` (default `3`)
- Face swap: `REPLICATE_IMAGE_MODEL` (default `google/nano-banana`) · `FACESWAP_IMAGES_KEY` (default `image_input`) · `FACESWAP_PROMPT`
- Text removal: `REPLICATE_TEXT_REMOVAL_MODEL` (default `black-forest-labs/flux-kontext-pro`) · `REPLICATE_TEXT_REMOVAL_IMAGE_KEY` (default `input_image`) · `REPLICATE_TEXT_REMOVAL_PROMPT_KEY` (default `prompt`) · `TEXT_REMOVAL_PROMPT`
- `REPLICATE_VIDEO_MODEL` — video face swap (currently gated off)
- Guardrails: `MAX_VIDEO_SECONDS` (`15`) · `MAX_FILE_MB` (`20`) · `DATA_DIR` (`./data`)

## Run
On the Pi (Docker) — helper scripts:
- `./scripts/start.sh` — build + start (checks Docker and `.env`)
- `./scripts/stop.sh` — stop
- `./scripts/logs.sh` — follow logs (Ctrl+C to exit)
- `./scripts/redeploy.sh` — `git pull --ff-only` + rebuild + restart

Raw equivalents: `docker compose up -d --build` / `docker compose down` / `docker compose logs -f`.

Local (without Docker) — env vars must be in the shell (the app reads the process env, not `.env`):
```bash
set -a && . ./.env && set +a
PYTHONPATH=src python -m memebot.main
```

## Commands
Registered as Telegram's command menu (☰ / `/` autocomplete) at startup. Each works as an
**image caption** or as a **follow-up message** to the last image you sent.

- `/text Oben | Unten` — meme text on image/video/GIF (`|` splits top/bottom; `/skip` leaves a line blank)
- `/face <Name>` — swap a saved face (image)
- `/clean` — remove text from an image
- `/recaption Oben | Unten` — clean, then add new text (image)
- `/gif <term>` — search GIFs on GIPHY (sends a few)
- `/meme` — random meme GIF
- `/clearchat` — delete the last ~100 messages (yours + the bot's, ≤48h)
- `/help` · `/start` — overview

## How it works
- **Local:** text overlay — Pillow for images, an ffmpeg-composited overlay for videos/GIFs
  (shared `draw_meme_text`).
- **Cloud (Replicate):** face swap (`nano-banana`) and text removal (`flux-kontext`) — **images
  only** in v1. On videos/GIFs only text is available; cloud edits there are deferred. Cloud calls
  run off the event loop and the model version is auto-resolved at startup.
- **GIFs:** GIPHY search/random; results can be forwarded back to the bot and captioned.
- **Costs (Replicate, ~cents/image):** face swap & text removal ≈ 4¢; text overlay & GIF search are free.

## Limitations
- Cloud edits (face swap / text removal) are image-only for now (video/GIF deferred).
- `/clearchat` can only delete messages **≤48h** old (Telegram limit).
- "Command → image" order (e.g. `/clean` *before* sending the image) isn't wired yet — send the
  image first, or attach the command as the image's caption.

## Tests
```bash
PYTHONPATH=src pytest -v
```

## Layout
```
src/memebot/
  config.py · main.py · replicate_io.py
  bot/        app.py · handlers.py · commands.py · keyboards.py · state.py
  renderer/   images.py · videos.py
  faceswap/   provider.py        textremove/ provider.py
  faces/      library.py         giphy/      client.py
docs/superpowers/{specs,plans}   scripts/{start,stop,logs,redeploy}.sh
```
