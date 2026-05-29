from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Text hinzufügen", callback_data="action:text")],
        [InlineKeyboardButton("🔁 Gesicht tauschen", callback_data="action:face")],
        [InlineKeyboardButton("✨ Beides", callback_data="action:both")],
        [InlineKeyboardButton("🧹 Text entfernen", callback_data="action:clean")],
        [InlineKeyboardButton("🆕 Vorlage neu betexten", callback_data="action:recaption")],
        [InlineKeyboardButton("❌ Abbrechen", callback_data="action:cancel")],
    ])


def faces_keyboard(names: list[str]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(n, callback_data=f"face:{n}")] for n in names]
    rows.append([InlineKeyboardButton(
        "➕ Neues Gesicht speichern", callback_data="face:__new__")])
    return InlineKeyboardMarkup(rows)
