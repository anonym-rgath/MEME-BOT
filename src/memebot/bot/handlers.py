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
from memebot.renderer.images import add_text_to_image
from memebot.renderer.videos import add_text_to_video, probe_duration
from memebot.bot.state import SessionStore
from memebot.bot.keyboards import action_keyboard, faces_keyboard


class Handlers:
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

    # --- guards -------------------------------------------------------
    def _allowed(self, update: Update) -> bool:
        user = update.effective_user
        return bool(user and self.s.is_allowed(user.id))

    def _tmp(self, suffix: str) -> str:
        os.makedirs(self.s.data_dir, exist_ok=True)
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.s.data_dir)
        os.close(fd)
        return path

    # --- entry points -------------------------------------------------
    async def start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return await update.message.reply_text("⛔ Nicht freigeschaltet.")
        await update.message.reply_text(
            "👋 Schick mir ein Bild oder Video, dann wählst du per Buttons, "
            "was ich daraus machen soll."
        )

    async def on_media(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return await update.message.reply_text("⛔ Nicht freigeschaltet.")
        msg = update.message
        chat_id = msg.chat_id
        sess = self.store.get(chat_id)

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

        await msg.reply_text("Was soll ich machen?", reply_markup=action_keyboard())

    async def on_button(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self._allowed(update):
            return
        q = update.callback_query
        await q.answer()
        chat_id = q.message.chat_id
        sess = self.store.get(chat_id)
        data = q.data

        if data == "action:cancel":
            self.store.clear(chat_id)
            return await q.edit_message_text("Abgebrochen.")

        if data.startswith("action:"):
            sess.action = data.split(":", 1)[1]
            # v1: video face swap is deferred — videos support text only.
            if sess.is_video and sess.action in ("face", "both"):
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
            # 1) face swap (cloud) if requested — images only in v1
            if sess.action in ("face", "both") and sess.chosen_face:
                face_path = self.faces.get_path(
                    self._user_for_chat(sess, chat_id), sess.chosen_face)
                swapped = await asyncio.to_thread(
                    self._swap, current, face_path, sess.is_video)
                local = self._tmp(".mp4" if sess.is_video else ".jpg")
                temp_files.append(local)
                urllib.request.urlretrieve(swapped, local)
                current = local
            # 2) text overlay (local) if requested
            if sess.action in ("text", "both") and (sess.top_text or sess.bottom_text):
                out = self._tmp(".mp4" if sess.is_video else ".jpg")
                temp_files.append(out)
                if sess.is_video:
                    add_text_to_video(current, out, sess.top_text, sess.bottom_text)
                else:
                    add_text_to_image(current, out, sess.top_text, sess.bottom_text)
                current = out
            # 3) send back
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
    def _user_for_chat(sess, chat_id):
        # In private chats chat_id == user_id, which is what the face library uses.
        return chat_id
