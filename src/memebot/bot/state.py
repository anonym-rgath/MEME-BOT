from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Session:
    media_path: str | None = None
    is_video: bool = False
    is_animation: bool = False  # GIF/animation → send result via send_animation
    action: str | None = None          # "text" | "face" | "both" | "clean" | "recaption"
    awaiting: str | None = None        # "top_text" | "bottom_text" | "face_name"
    top_text: str | None = None
    bottom_text: str | None = None
    chosen_face: str | None = None
    pending_face_path: str | None = None  # a face photo waiting to be named


class SessionStore:
    def __init__(self):
        self._sessions: dict[int, Session] = {}

    def get(self, chat_id: int) -> Session:
        return self._sessions.setdefault(chat_id, Session())

    def clear(self, chat_id: int) -> None:
        self._sessions.pop(chat_id, None)
