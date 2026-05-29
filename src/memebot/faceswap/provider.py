from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class FaceSwapProvider(Protocol):
    def swap_image(self, target_path: str, face_path: str) -> str: ...
    def swap_video(self, target_path: str, face_path: str) -> str: ...


class ReplicateProvider:
    """Face swap via Replicate. `client` defaults to the real replicate module.

    NOTE: the `input` keys (input_image / swap_image) depend on the chosen
    model. Verify the current model's schema on replicate.com and adjust the
    two `_run` calls if the model expects different key names.
    """

    def __init__(self, client, image_model: str, video_model: str):
        self._client = client
        self._image_model = image_model
        self._video_model = video_model

    def _run(self, model: str, target_path: str, face_path: str) -> str:
        with open(target_path, "rb") as target, open(face_path, "rb") as face:
            output = self._client.run(
                model,
                input={"input_image": target, "swap_image": face},
            )
        return first_url(output)

    def swap_image(self, target_path: str, face_path: str) -> str:
        return self._run(self._image_model, target_path, face_path)

    def swap_video(self, target_path: str, face_path: str) -> str:
        return self._run(self._video_model, target_path, face_path)
