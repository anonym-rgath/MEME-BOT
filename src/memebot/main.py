from __future__ import annotations
import logging
from memebot.config import Settings
from memebot.bot.app import build_application


def main():
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    app = build_application(settings)
    logging.info("Meme-Bot starting (long polling)…")
    app.run_polling()


if __name__ == "__main__":
    main()
