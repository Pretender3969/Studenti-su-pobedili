"""Crta ikone sajta: beli broj 3 na crvenoj pozadini, debelim sistemskim fontom (potreban Pillow)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BG, FG = (200, 16, 46), (255, 255, 255)
FONT = "C:/Windows/Fonts/ariblk.ttf"  # Arial Black


def icon(size, radius=0.0):
    big = size * 4  # crtamo uvećano pa smanjujemo, zbog glatkih ivica
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=int(big * radius), fill=BG)
    font = ImageFont.truetype(FONT, int(big * 0.78))
    l, t, r, b = d.textbbox((0, 0), "3", font=font)
    d.text(((big - (r - l)) / 2 - l, (big - (b - t)) / 2 - t), "3", font=font, fill=FG)
    return img.resize((size, size), Image.LANCZOS)


# ikone za telefon su pune kvadratne (sistem sam zaobljava ivice), mala ikona ima zaobljene uglove
for s in (192, 512):
    icon(s).convert("RGB").save(ROOT / "assets" / f"ikona-{s}.png", optimize=True)
icon(64, radius=0.18).save(ROOT / "assets" / "ikona-64.png", optimize=True)
