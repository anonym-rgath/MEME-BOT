from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Try a few common bundled fonts, fall back to PIL default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # linux/pi
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",     # macOS
        "/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_centered(draw, text, font, img_w, y, stroke=2):
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    text_w = bbox[2] - bbox[0]
    x = (img_w - text_w) / 2
    draw.text(
        (x, y), text, font=font, fill="white",
        stroke_width=stroke, stroke_fill="black",
    )


def draw_meme_text(image: "Image.Image", top: str | None, bottom: str | None) -> None:
    """Draw classic white/black-outline meme text top/bottom onto `image` in place."""
    draw = ImageDraw.Draw(image)
    font = _load_font(max(16, image.height // 10))
    if top:
        _draw_centered(draw, top.upper(), font, image.width, y=image.height * 0.03)
    if bottom:
        bbox = draw.textbbox((0, 0), bottom.upper(), font=font, stroke_width=2)
        text_h = bbox[3] - bbox[1]
        _draw_centered(
            draw, bottom.upper(), font, image.width,
            y=image.height - text_h - image.height * 0.06,
        )


def add_text_to_image(
    src_path: str,
    out_path: str,
    top: str | None = None,
    bottom: str | None = None,
) -> str:
    """Draw classic meme top/bottom text on an image. Returns out_path."""
    with Image.open(src_path) as im:
        im = im.convert("RGB")
        draw_meme_text(im, top, bottom)
        im.save(out_path, format="JPEG", quality=90)
    return out_path
