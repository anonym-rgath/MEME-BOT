from pathlib import Path
from PIL import Image
from memebot.renderer.images import add_text_to_image

def _make_sample(tmp_path) -> Path:
    p = tmp_path / "in.jpg"
    Image.new("RGB", (400, 300), color=(120, 120, 120)).save(p)
    return p

def test_returns_path_and_writes_file(tmp_path):
    src = _make_sample(tmp_path)
    out = tmp_path / "out.jpg"
    result = add_text_to_image(str(src), str(out), top="HELLO", bottom="WORLD")
    assert result == str(out)
    assert out.exists()

def test_output_is_valid_image_same_size(tmp_path):
    src = _make_sample(tmp_path)
    out = tmp_path / "out.jpg"
    add_text_to_image(str(src), str(out), top="TOP", bottom=None)
    with Image.open(out) as im:
        assert im.size == (400, 300)

def test_changes_pixels(tmp_path):
    src = _make_sample(tmp_path)
    out = tmp_path / "out.jpg"
    add_text_to_image(str(src), str(out), top="X", bottom="Y")
    before = list(Image.open(src).getdata())
    after = list(Image.open(out).getdata())
    assert before != after  # text was drawn
