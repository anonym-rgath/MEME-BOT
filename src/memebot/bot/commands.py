from __future__ import annotations
from dataclasses import dataclass

_KNOWN = {"text", "face", "clean", "recaption"}

_USAGE = {
    "text": "Usage: /text Oben | Unten",
    "recaption": "Usage: /recaption Oben | Unten",
    "face": "Usage: /face <Name>",
}


@dataclass
class ParsedCommand:
    action: str
    top: str | None = None
    bottom: str | None = None
    face: str | None = None
    error: str | None = None


def _split_text(rest: str) -> tuple[str | None, str | None]:
    if "|" in rest:
        top, bottom = rest.split("|", 1)
        return (top.strip() or None), (bottom.strip() or None)
    return (rest.strip() or None), None


def parse_command(raw: str) -> ParsedCommand | None:
    """Parse a command line into a ParsedCommand, or None if not a known command."""
    raw = (raw or "").strip()
    if not raw.startswith("/"):
        return None
    head, _, rest = raw[1:].partition(" ")
    cmd = head.split("@", 1)[0].lower()  # strip optional @botname suffix
    if cmd not in _KNOWN:
        return None
    if cmd == "clean":
        return ParsedCommand(action="clean")
    if cmd == "face":
        name = rest.strip()
        if not name:
            return ParsedCommand(action="face", error=_USAGE["face"])
        return ParsedCommand(action="face", face=name)
    # text | recaption
    top, bottom = _split_text(rest)
    if not top and not bottom:
        return ParsedCommand(action=cmd, error=_USAGE[cmd])
    return ParsedCommand(action=cmd, top=top, bottom=bottom)
