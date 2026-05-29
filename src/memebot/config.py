from __future__ import annotations
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    allowed_users: frozenset[int]
    replicate_api_token: str
    image_model: str = "cdingram/face-swap"
    video_model: str = "arabyai-replicate/roop_face_swap"
    text_removal_model: str = "black-forest-labs/flux-kontext-pro"
    text_removal_prompt: str = (
        "Remove all text, letters, captions and watermarks from the image. "
        "Keep everything else exactly the same."
    )
    text_removal_image_key: str = "input_image"
    text_removal_prompt_key: str = "prompt"
    max_video_seconds: int = 15
    max_file_mb: int = 20
    data_dir: str = "./data"
    giphy_api_key: str = ""
    giphy_result_count: int = 3

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        env = env if env is not None else dict(os.environ)

        def required(key: str) -> str:
            val = env.get(key, "").strip()
            if not val:
                raise ValueError(f"Missing required env var: {key}")
            return val

        users_raw = env.get("TELEGRAM_ALLOWED_USERS", "")
        allowed = frozenset(
            int(part.strip()) for part in users_raw.split(",") if part.strip()
        )
        return cls(
            telegram_bot_token=required("TELEGRAM_BOT_TOKEN"),
            allowed_users=allowed,
            replicate_api_token=required("REPLICATE_API_TOKEN"),
            image_model=env.get("REPLICATE_IMAGE_MODEL", cls.image_model),
            video_model=env.get("REPLICATE_VIDEO_MODEL", cls.video_model),
            text_removal_model=env.get("REPLICATE_TEXT_REMOVAL_MODEL", cls.text_removal_model),
            text_removal_prompt=env.get("TEXT_REMOVAL_PROMPT", cls.text_removal_prompt),
            text_removal_image_key=env.get("REPLICATE_TEXT_REMOVAL_IMAGE_KEY", cls.text_removal_image_key),
            text_removal_prompt_key=env.get("REPLICATE_TEXT_REMOVAL_PROMPT_KEY", cls.text_removal_prompt_key),
            max_video_seconds=int(env.get("MAX_VIDEO_SECONDS", cls.max_video_seconds)),
            max_file_mb=int(env.get("MAX_FILE_MB", cls.max_file_mb)),
            data_dir=env.get("DATA_DIR", cls.data_dir),
            giphy_api_key=env.get("GIPHY_API_KEY", cls.giphy_api_key),
            giphy_result_count=int(env.get("GIPHY_RESULT_COUNT", cls.giphy_result_count)),
        )

    def is_allowed(self, user_id: int) -> bool:
        return user_id in self.allowed_users
