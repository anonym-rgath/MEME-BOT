from __future__ import annotations
import replicate
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
)

from memebot.config import Settings
from memebot.faces.library import FaceLibrary
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

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("skip", handlers.on_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handlers.on_media))
    app.add_handler(CallbackQueryHandler(handlers.on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))
    return app
