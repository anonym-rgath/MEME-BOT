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

def test_text_removal_defaults_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    s = Settings.from_env(base)
    assert s.text_removal_model == "black-forest-labs/flux-kontext-pro"
    assert "text" in s.text_removal_prompt.lower()
    assert s.text_removal_image_key == "input_image"
    assert s.text_removal_prompt_key == "prompt"
    s2 = Settings.from_env({**base,
        "REPLICATE_TEXT_REMOVAL_MODEL": "owner/model",
        "TEXT_REMOVAL_PROMPT": "erase text",
        "REPLICATE_TEXT_REMOVAL_IMAGE_KEY": "image",
        "REPLICATE_TEXT_REMOVAL_PROMPT_KEY": "instruction"})
    assert s2.text_removal_model == "owner/model"
    assert s2.text_removal_prompt == "erase text"
    assert s2.text_removal_image_key == "image"
    assert s2.text_removal_prompt_key == "instruction"

def test_faceswap_defaults_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    s = Settings.from_env(base)
    assert s.image_model == "google/nano-banana"
    assert s.faceswap_images_key == "image_input"
    assert "face" in s.faceswap_prompt.lower()
    s2 = Settings.from_env({**base,
        "REPLICATE_IMAGE_MODEL": "owner/model",
        "FACESWAP_PROMPT": "swap it",
        "FACESWAP_IMAGES_KEY": "image_urls"})
    assert s2.image_model == "owner/model"
    assert s2.faceswap_prompt == "swap it"
    assert s2.faceswap_images_key == "image_urls"

def test_giphy_key_default_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    assert Settings.from_env(base).giphy_api_key == ""
    s = Settings.from_env({**base, "GIPHY_API_KEY": "gk"})
    assert s.giphy_api_key == "gk"

def test_giphy_result_count_default_and_override():
    base = {"TELEGRAM_BOT_TOKEN": "t", "REPLICATE_API_TOKEN": "r"}
    assert Settings.from_env(base).giphy_result_count == 3
    assert Settings.from_env({**base, "GIPHY_RESULT_COUNT": "5"}).giphy_result_count == 5
