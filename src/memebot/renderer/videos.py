from __future__ import annotations
import json
import subprocess


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", path],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def _escape(text: str) -> str:
    # ffmpeg drawtext needs these escaped
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "'")


def _drawtext_filter(text: str, y_expr: str) -> str:
    t = _escape(text.upper())
    return (
        f"drawtext=text='{t}':fontcolor=white:borderw=3:bordercolor=black"
        f":fontsize=h/12:x=(w-text_w)/2:y={y_expr}"
    )


def add_text_to_video(
    src_path: str,
    out_path: str,
    top: str | None = None,
    bottom: str | None = None,
) -> str:
    """Burn meme top/bottom text into a video via ffmpeg drawtext. Returns out_path."""
    filters = []
    if top:
        filters.append(_drawtext_filter(top, y_expr="h*0.05"))
    if bottom:
        filters.append(_drawtext_filter(bottom, y_expr="h-text_h-h*0.08"))
    vf = ",".join(filters) if filters else "null"

    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-vf", vf,
         "-codec:a", "copy", out_path],
        check=True, capture_output=True,
    )
    return out_path
