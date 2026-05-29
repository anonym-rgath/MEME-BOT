from __future__ import annotations
import json
import os
import subprocess

from PIL import Image
from memebot.renderer.images import draw_meme_text


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", path],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def _video_size(path: str) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", path],
        check=True, capture_output=True, text=True,
    )
    streams = json.loads(out.stdout)["streams"]
    video = next(s for s in streams if s.get("codec_type") == "video")
    return int(video["width"]), int(video["height"])


def add_text_to_video(
    src_path: str,
    out_path: str,
    top: str | None = None,
    bottom: str | None = None,
) -> str:
    """Burn meme top/bottom text into a video by compositing a Pillow-rendered
    transparent overlay onto it via ffmpeg's `overlay` filter (no libfreetype
    dependency). Returns out_path."""
    if not top and not bottom:
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-codec", "copy", out_path],
            check=True, capture_output=True,
        )
        return out_path

    width, height = _video_size(src_path)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_meme_text(overlay, top, bottom)

    tmp_png = out_path + ".overlay.png"
    overlay.save(tmp_png)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-i", tmp_png,
             "-filter_complex", "[0:v][1:v]overlay=0:0[v]",
             "-map", "[v]", "-map", "0:a?",
             "-codec:a", "copy", out_path],
            check=True, capture_output=True,
        )
    finally:
        try:
            os.remove(tmp_png)
        except OSError:
            pass
    return out_path
