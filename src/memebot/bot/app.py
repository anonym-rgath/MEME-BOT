from __future__ import annotations
import logging
import replicate
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
)

from memebot.config import Settings
from memebot.faces.library import FaceLibrary
from memebot.faceswap.provider import ReplicateProvider
from memebot.textremove.provider import ReplicateTextRemover
from memebot.bot.handlers import Handlers

log = logging.getLogger(__name__)


def _pinned(client, ref: str) -> str:
    """Replicate community models must be run by a specific version (owner/model:id),
    not by bare name (that endpoint is for official models only → 404). If `ref` has
    no ':version', resolve the model's latest version once at startup. Falls back to
    the bare ref on lookup failure (e.g. Replicate unreachable) so the bot still starts
    for text/button use; a real call would then surface the error."""
    if ":" in ref:
        return ref
    try:
        version = client.models.get(ref).latest_version
        if version is not None:
            return f"{ref}:{version.id}"
        log.warning("Replicate model %s has no runnable version; using bare ref", ref)
    except Exception as exc:  # network / unknown model
        log.warning("Could not resolve Replicate version for %s: %s", ref, exc)
    return ref


def build_application(settings: Settings) -> Application:
    client = replicate.Client(api_token=settings.replicate_api_token)
    swapper = ReplicateProvider(
        client=client,
        image_model=_pinned(client, settings.image_model),
        video_model=settings.video_model,  # bare ref; video face-swap is gated off in v1
    )
    text_remover = ReplicateTextRemover(
        client=client,
        model=_pinned(client, settings.text_removal_model),
        instruction=settings.text_removal_prompt,
        image_key=settings.text_removal_image_key,
        prompt_key=settings.text_removal_prompt_key,
    )
    handlers = Handlers(
        settings=settings,
        faces=FaceLibrary(settings.data_dir),
        swapper=swapper,
        text_remover=text_remover,
    )

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help))
    app.add_handler(CommandHandler("skip", handlers.on_text))
    app.add_handler(CommandHandler(["text", "face", "clean", "recaption"], handlers.on_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handlers.on_media))
    app.add_handler(CallbackQueryHandler(handlers.on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.on_text))
    return app
