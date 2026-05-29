from __future__ import annotations
import replicate
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
)

from memebot.config import Settings
from memebot.faces.library import FaceLibrary
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

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("skip", handlers.on_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handlers.on_media))
    app.add_handler(CallbackQueryHandler(handlers.on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))
    return app
