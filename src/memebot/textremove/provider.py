from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class TextRemovalProvider(Protocol):
    def remove_text(self, image_path: str) -> str: ...


class ReplicateTextRemover:
    """Remove text from an image via a text-guided Replicate model.

    The input field names differ per model, so they are configurable:
    - black-forest-labs/flux-kontext-pro → image_key="input_image", prompt_key="prompt"
    - qwen/qwen-image-edit → image_key="image", prompt_key="prompt"
    - adirik/inst-inpaint → image_key="image", prompt_key="instruction"
    """

    def __init__(
        self,
        client,
        model: str,
        instruction: str,
        image_key: str = "input_image",
        prompt_key: str = "prompt",
    ):
        self._client = client
        self._model = model
        self._instruction = instruction
        self._image_key = image_key
        self._prompt_key = prompt_key

    def remove_text(self, image_path: str) -> str:
        with open(image_path, "rb") as image:
            output = self._client.run(
                self._model,
                input={self._image_key: image, self._prompt_key: self._instruction},
            )
        return first_url(output)
