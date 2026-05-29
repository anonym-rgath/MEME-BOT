from memebot.bot.commands import parse_command, ParsedCommand

def test_unknown_returns_none():
    assert parse_command("hello") is None
    assert parse_command("/unknown foo") is None
    assert parse_command("") is None

def test_clean():
    p = parse_command("/clean")
    assert p.action == "clean" and p.error is None

def test_text_top_and_bottom():
    p = parse_command("/text Hello | World")
    assert p.action == "text"
    assert p.top == "Hello"
    assert p.bottom == "World"
    assert p.error is None

def test_text_top_only():
    p = parse_command("/text Just top")
    assert p.action == "text"
    assert p.top == "Just top"
    assert p.bottom is None

def test_text_empty_is_error():
    p = parse_command("/text")
    assert p.action == "text"
    assert p.error is not None

def test_text_pipe_with_empty_sides_is_error():
    p = parse_command("/text   |   ")
    assert p.action == "text"
    assert p.top is None
    assert p.bottom is None
    assert p.error is not None

def test_face_with_name():
    p = parse_command("/face Robin")
    assert p.action == "face"
    assert p.face == "Robin"
    assert p.error is None

def test_face_without_name_is_error():
    p = parse_command("/face")
    assert p.action == "face"
    assert p.error is not None

def test_recaption():
    p = parse_command("/recaption Top | Bottom")
    assert p.action == "recaption"
    assert p.top == "Top"
    assert p.bottom == "Bottom"

def test_strips_bot_mention():
    p = parse_command("/clean@MyMemeBot")
    assert p.action == "clean"

def test_leading_trailing_whitespace():
    p = parse_command("  /text  A | B  ")
    assert p.action == "text"
    assert p.top == "A"
    assert p.bottom == "B"
