from memebot.bot.state import Session, SessionStore

def test_store_creates_and_returns_session():
    store = SessionStore()
    s = store.get(chat_id=5)
    assert isinstance(s, Session)
    assert store.get(5) is s  # same instance on repeat

def test_session_holds_media_and_action():
    store = SessionStore()
    s = store.get(5)
    s.media_path = "/tmp/x.jpg"
    s.is_video = False
    s.action = "text"
    assert store.get(5).media_path == "/tmp/x.jpg"
    assert store.get(5).action == "text"

def test_clear_removes_session():
    store = SessionStore()
    store.get(5).action = "text"
    store.clear(5)
    assert store.get(5).action is None  # fresh session
