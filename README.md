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
- Local: `PYTHONPATH=src python -m memebot.main`
- Docker: `docker compose up -d --build`

## Tests
`PYTHONPATH=src pytest -v`
