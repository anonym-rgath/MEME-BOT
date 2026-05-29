from pathlib import Path
from memebot.faces.library import FaceLibrary

def test_save_and_list(tmp_path):
    lib = FaceLibrary(str(tmp_path))
    src = tmp_path / "photo.jpg"
    src.write_bytes(b"fake-jpeg-bytes")
    lib.save(user_id=42, name="Robin", src_path=str(src))
    assert lib.list_names(42) == ["Robin"]
    assert lib.list_names(99) == []

def test_get_path_roundtrip(tmp_path):
    lib = FaceLibrary(str(tmp_path))
    src = tmp_path / "photo.jpg"
    src.write_bytes(b"data")
    lib.save(42, "Robin", str(src))
    stored = lib.get_path(42, "Robin")
    assert Path(stored).exists()
    assert Path(stored).read_bytes() == b"data"

def test_get_missing_returns_none(tmp_path):
    lib = FaceLibrary(str(tmp_path))
    assert lib.get_path(42, "Nope") is None

def test_names_are_sanitized(tmp_path):
    lib = FaceLibrary(str(tmp_path))
    src = tmp_path / "p.jpg"
    src.write_bytes(b"x")
    lib.save(42, "../evil name!", str(src))
    names = lib.list_names(42)
    assert names == ["evil name"]
