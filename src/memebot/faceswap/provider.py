from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class FaceSwapProvider(Protocol):
    def swap_image(self, target_path: str, face_path: str) -> str: ...
    def swap_video(self, target_path: str, face_path: str) -> str: ...


class ReplicateProvider:
    """Face swap via Replicate.

    Images use a generative editor (default google/nano-banana): the target and
    the face are passed as an image array plus an instruction prompt. The image
    array field name is configurable (`images_key`) so models can be swapped
    via env without code changes (Replicate nano-banana = `image_input`).

    Video swap keeps the older inswapper-style call (`input_image`/`swap_image`);
    it is gated off in the bot for now.
    """

    def __init__(
        self,
        client,
        image_model: str,
        video_model: str,
        faceswap_prompt: str,
        images_key: str = "image_input",
    ):
        self._client = client
        self._image_model = image_model
        self._video_model = video_model
        self._prompt = faceswap_prompt
        self._images_key = images_key

    def swap_image(self, target_path: str, face_path: str) -> str:
        with open(target_path, "rb") as target, open(face_path, "rb") as face:
            output = self._client.run(
                self._image_model,
                input={"prompt": self._prompt, self._images_key: [target, face]},
            )
        return first_url(output)

    def swap_video(self, target_path: str, face_path: str) -> str:
        with open(target_path, "rb") as target, open(face_path, "rb") as face:
            output = self._client.run(
                self._video_model,
                input={"input_image": target, "swap_image": face},
            )
        return first_url(output)
