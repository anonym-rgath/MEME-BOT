from __future__ import annotations
import re
import shutil
from pathlib import Path


def _sanitize(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _-]", "", name).strip()
    return cleaned or "face"


class FaceLibrary:
    """Per-user face image storage under <root>/<user_id>/<name>.jpg."""

    def __init__(self, root: str):
        self._root = Path(root) / "faces"

    def _user_dir(self, user_id: int) -> Path:
        d = self._root / str(user_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, user_id: int, name: str, src_path: str) -> str:
        safe = _sanitize(name)
        dest = self._user_dir(user_id) / f"{safe}.jpg"
        shutil.copyfile(src_path, dest)
        return str(dest)

    def list_names(self, user_id: int) -> list[str]:
        d = self._root / str(user_id)
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.jpg"))

    def get_path(self, user_id: int, name: str) -> str | None:
        p = self._root / str(user_id) / f"{_sanitize(name)}.jpg"
        return str(p) if p.exists() else None
