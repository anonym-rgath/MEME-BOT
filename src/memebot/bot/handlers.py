from __future__ import annotations
import asyncio
import os
import tempfile
import urllib.request

from telegram import Update
from telegram.ext import ContextTypes

from memebot.config import Settings
from memebot.faces.library import FaceLibrary
from memebot.faceswap.provider import FaceSwapProvider
from memebot.textremove.provider import TextRemovalProvider
from memebot.giphy.client import GiphyClient
from memebot.renderer.images import add_text_to_image
from memebot.renderer.videos import add_text_to_video
from memebot.bot.state import SessionStore
from memebot.bot.keyboards import action_keyboard, faces_keyboard
from memebot.bot.commands import parse_command

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


class Handlers:
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

    # --- guards -------------------------------------------------------
    def _allowed(self, update: Update) -> bool:
        user = update.effective_user
        return bool(user and self.s.is_allowed(user.id))

    def _tmp(self, suffix: str) -> str:
        os.makedirs(self.s.data_dir, exist_ok=True)
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.s.data_dir)
        os.close(fd)
        return path

    def _discard_session_media(self, sess) -> None:
        """Delete any on-disk temp files this session still holds (early-exit cleanup)."""
        for path in (sess.media_path, sess.pending_face_path):
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass

    # --- entry points -------------------------------------------------
    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return await update.message.reply_text("⛔ Nicht freigeschaltet.")
        await update.message.reply_text(
            "👋 Schick mir ein Bild oder Video, dann wählst du per Buttons, "
            "was ich daraus machen soll.\n\n" + HELP_TEXT
        )

    async def help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        await update.message.reply_text(HELP_TEXT)

    async def on_media(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return await update.message.reply_text("⛔ Nicht freigeschaltet.")
        msg = update.message
        chat_id = msg.chat_id
        sess = self.store.get(chat_id)

        # a new upload supersedes any half-finished flow — drop stale temp files
        self._discard_session_media(sess)
        sess.pending_face_path = None

        if msg.photo:
            tg_file = await msg.photo[-1].get_file()
            sess.media_path = self._tmp(".jpg")
            sess.is_video = False
        elif msg.video:
            if msg.video.duration and msg.video.duration > self.s.max_video_seconds:
                return await msg.reply_text(
                    f"⏱ Video zu lang (max {self.s.max_video_seconds}s).")
            tg_file = await msg.video.get_file()
            sess.media_path = self._tmp(".mp4")
            sess.is_video = True
        else:
            return

        await tg_file.download_to_drive(sess.media_path)

        # If a face name was awaited, this photo is a face to store instead.
        if sess.awaiting == "face_name_photo":
            sess.pending_face_path = sess.media_path
            sess.awaiting = "face_name"
            return await msg.reply_text("Wie soll dieses Gesicht heißen?")

        # Caption command (e.g. "/text Oben | Unten") → run directly, skip buttons.
        if msg.caption:
            parsed = parse_command(msg.caption)
            if parsed is not None:
                return await self._run_command(chat_id, sess, parsed, ctx)

        await msg.reply_text("Was soll ich machen?", reply_markup=action_keyboard())

    async def on_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        msg = update.message
        sess = self.store.get(msg.chat_id)
        parsed = parse_command(msg.text)
        if parsed is None:
            return
        if sess.media_path is None:
            return await msg.reply_text("📷 Schick mir zuerst ein Bild.")
        await self._run_command(msg.chat_id, sess, parsed, ctx)

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

    async def _run_command(self, chat_id, sess, parsed, ctx):
        if parsed.error:
            return await ctx.bot.send_message(chat_id, parsed.error)
        # v1: cloud edits (face swap, text removal) are image-only.
        if sess.is_video and parsed.action in ("face", "clean", "recaption"):
            self._discard_session_media(sess)
            self.store.clear(chat_id)
            return await ctx.bot.send_message(
                chat_id,
                "🪄 Cloud-Bearbeitung (Gesicht tauschen / Text entfernen) für "
                "Videos kommt später. Bei Videos geht aktuell nur /text.")
        sess.action = parsed.action
        sess.top_text = parsed.top
        sess.bottom_text = parsed.bottom
        sess.chosen_face = parsed.face
        await ctx.bot.send_message(chat_id, "⏳ Verarbeite…")
        await self._process_and_send(chat_id, sess, ctx)

    async def on_button(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        q = update.callback_query
        await q.answer()
        chat_id = q.message.chat_id
        sess = self.store.get(chat_id)
        data = q.data

        if data == "action:cancel":
            self._discard_session_media(sess)
            self.store.clear(chat_id)
            return await q.edit_message_text("Abgebrochen.")

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

        if data.startswith("face:"):
            name = data.split(":", 1)[1]
            if name == "__new__":
                sess.awaiting = "face_name_photo"
                return await q.edit_message_text(
                    "Schick mir jetzt ein Foto des Gesichts.")
            sess.chosen_face = name
            return await self._run_pipeline(q, sess, ctx)

    async def on_text(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        msg = update.message
        sess = self.store.get(msg.chat_id)
        text = msg.text

        if sess.awaiting == "face_name":
            self.faces.save(
                update.effective_user.id, text, sess.pending_face_path)
            try:  # remove the temp upload; the library keeps its own copy
                os.remove(sess.pending_face_path)
            except OSError:
                pass
            sess.pending_face_path = None
            sess.awaiting = None
            return await msg.reply_text(f"✅ Gesicht „{text}” gespeichert.")

        if sess.awaiting == "top_text":
            sess.top_text = None if text == "/skip" else text
            sess.awaiting = "bottom_text"
            return await msg.reply_text("Text unten? (oder /skip für keinen)")

        if sess.awaiting == "bottom_text":
            sess.bottom_text = None if text == "/skip" else text
            sess.awaiting = None
            if sess.action == "both":
                return await self._prompt_faces_msg(msg, sess)
            return await self._run_pipeline_msg(msg, sess, ctx)

    # --- face prompt helpers -----------------------------------------
    async def _prompt_faces(self, q, sess):
        names = self.faces.list_names(q.from_user.id)
        await q.edit_message_text(
            "Welches Gesicht?", reply_markup=faces_keyboard(names))

    async def _prompt_faces_msg(self, msg, sess):
        names = self.faces.list_names(msg.from_user.id)
        await msg.reply_text(
            "Welches Gesicht?", reply_markup=faces_keyboard(names))

    # --- pipeline -----------------------------------------------------
    async def _run_pipeline(self, q, sess, ctx):
        await q.edit_message_text("⏳ Verarbeite…")
        await self._process_and_send(q.message.chat_id, sess, ctx)

    async def _run_pipeline_msg(self, msg, sess, ctx):
        await msg.reply_text("⏳ Verarbeite…")
        await self._process_and_send(msg.chat_id, sess, ctx)

    async def _process_and_send(self, chat_id, sess, ctx):
        temp_files: list[str] = []
        if sess.media_path:
            temp_files.append(sess.media_path)
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
                face_path = self.faces.get_path(
                    self._user_for_chat(chat_id), sess.chosen_face)
                if face_path is None:
                    raise RuntimeError("Gewähltes Gesicht nicht gefunden.")
                swapped = await asyncio.to_thread(
                    self._swap, current, face_path, sess.is_video)
                local = self._tmp(".mp4" if sess.is_video else ".jpg")
                temp_files.append(local)
                await asyncio.to_thread(urllib.request.urlretrieve, swapped, local)
                current = local
            # 3) text overlay (local) if requested
            if sess.action in ("text", "both", "recaption") and (sess.top_text or sess.bottom_text):
                out = self._tmp(".mp4" if sess.is_video else ".jpg")
                temp_files.append(out)
                if sess.is_video:
                    add_text_to_video(current, out, sess.top_text, sess.bottom_text)
                else:
                    add_text_to_image(current, out, sess.top_text, sess.bottom_text)
                current = out
            # 4) send back
            if sess.is_video:
                with open(current, "rb") as f:
                    await ctx.bot.send_video(chat_id, video=f)
            else:
                with open(current, "rb") as f:
                    await ctx.bot.send_photo(chat_id, photo=f)
        except Exception as exc:  # surface a friendly error
            await ctx.bot.send_message(chat_id, f"⚠️ Fehler: {exc}")
        finally:
            # privacy: delete all temp uploads/results; saved library faces persist
            for path in temp_files:
                try:
                    os.remove(path)
                except OSError:
                    pass
            self.store.clear(chat_id)

    def _swap(self, target, face, is_video):
        if is_video:
            return self.swapper.swap_video(target, face)
        return self.swapper.swap_image(target, face)

    @staticmethod
    def _user_for_chat(chat_id):
        # In private chats chat_id == user_id, which is what the face library uses.
        return chat_id
