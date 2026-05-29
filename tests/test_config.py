import pytest
from memebot.config import Settings

def test_loads_from_env_dict():
    env = {
        "TELEGRAM_BOT_TOKEN": "tok",
        "TELEGRAM_ALLOWED_USERS": "111, 222",
        "REPLICATE_API_TOKEN": "rep",
        "DATA_DIR": "/tmp/memebot",
    }
    s = Settings.from_env(env)
    assert s.telegram_bot_token == "tok"
    assert s.allowed_users == {111, 222}
    assert s.replicate_api_token == "rep"
    assert s.max_video_seconds == 15  # default
    assert s.data_dir == "/tmp/memebot"

def test_missing_token_raises():
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Settings.from_env({"TELEGRAM_ALLOWED_USERS": "1"})

def test_is_allowed():
    s = Settings.from_env({
        "TELEGRAM_BOT_TOKEN": "tok",
        "TELEGRAM_ALLOWED_USERS": "111",
        "REPLICATE_API_TOKEN": "rep",
    })
    assert s.is_allowed(111) is True
    assert s.is_allowed(999) is False
