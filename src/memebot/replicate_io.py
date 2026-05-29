from __future__ import annotations


def first_url(output) -> str:
    """Normalize a Replicate result (str | list | file-like with .url) to one URL string."""
    if isinstance(output, list):
        output = output[0]
    if isinstance(output, str):
        return output
    return getattr(output, "url", str(output))
