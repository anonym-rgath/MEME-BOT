# MEME-BOT

Telegram bot to add meme text and swap faces on images and videos.
Long-polling, runs as a Docker container (e.g. on the Raspberry Pi).

## Setup
1. Create a bot via @BotFather → copy the token.
2. Create a Replicate account → copy the API token from replicate.com/account.
3. Find your numeric Telegram user ID (e.g. via @userinfobot).
4. `cp .env.example .env` and fill in the values (TELEGRAM_BOT_TOKEN,
   TELEGRAM_ALLOWED_USERS, REPLICATE_API_TOKEN).
5. Verify the Replicate model slugs in `.env` are current (replicate.com).

## Run

On the Pi (Docker) — use the helper scripts:
- `./scripts/start.sh` — build + start the container (checks Docker and `.env`)
- `./scripts/stop.sh` — stop the container
- `./scripts/logs.sh` — follow the bot logs (Ctrl+C to exit)

Equivalent raw commands: `docker compose up -d --build` / `docker compose down` / `docker compose logs -f`.

Local (without Docker), the env vars must be in your shell — the app reads the
process environment, not `.env` directly:
```bash
set -a && . ./.env && set +a
PYTHONPATH=src python -m memebot.main
```

## Commands

Besides the buttons, you can drive the bot with commands — either as an image
caption or as a follow-up message to the last image you sent:

- `/text Oben | Unten` — add meme text (image or video)
- `/face <Name>` — swap a saved face (image)
- `/clean` — remove text (image)
- `/recaption Oben | Unten` — clean then add new text (image)
- `/gif <term>` — search a GIF on GIPHY
- `/meme` — random meme GIF
- `/help` — show this list

## Tests
`PYTHONPATH=src pytest -v`
