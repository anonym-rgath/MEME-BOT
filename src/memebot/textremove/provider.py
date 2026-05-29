from __future__ import annotations
from typing import Protocol

from memebot.replicate_io import first_url


class TextRemovalProvider(Protocol):
    def remove_text(self, image_path: str) -> str: ...


class ReplicateTextRemover:
    """Remove text from an image via a text-guided Replicate model.

    NOTE: input keys (`image` / `instruction`) depend on the chosen model. Verify the
    current model's schema on replicate.com and adjust the `input={...}` dict if needed.
    (adirik/inst-inpaint expects `image` + `instruction`.)
    """

    def __init__(self, client, model: str, instruction: str):
        self._client = client
        self._model = model
        self._instruction = instruction

    def remove_text(self, image_path: str) -> str:
        with open(image_path, "rb") as image:
            output = self._client.run(
                self._model,
                input={"image": image, "instruction": self._instruction},
            )
        return first_url(output)
