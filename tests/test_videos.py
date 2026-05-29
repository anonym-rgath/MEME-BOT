import shutil
import subprocess
from pathlib import Path
import pytest
from memebot.renderer.videos import add_text_to_video, probe_duration

ffmpeg_missing = shutil.which("ffmpeg") is None
pytestmark = pytest.mark.skipif(ffmpeg_missing, reason="ffmpeg not installed")

def _make_clip(path: Path, seconds: int = 1):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"testsrc=duration={seconds}:size=320x240:rate=10",
         str(path)],
        check=True, capture_output=True,
    )

def test_probe_duration(tmp_path):
    clip = tmp_path / "in.mp4"
    _make_clip(clip, seconds=2)
    assert 1.5 < probe_duration(str(clip)) < 2.5

def test_add_text_creates_output(tmp_path):
    clip = tmp_path / "in.mp4"
    out = tmp_path / "out.mp4"
    _make_clip(clip)
    result = add_text_to_video(str(clip), str(out), top="HELLO", bottom="WORLD")
    assert result == str(out)
    assert out.exists() and out.stat().st_size > 0
