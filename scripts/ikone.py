"""Crta ikone sajta (lista vesti sa crvenom tačkom) bez spoljnih biblioteka."""
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG, FG, RED = (43, 58, 140), (255, 255, 255), (230, 72, 60)
# pravougaonici u jedinicama 0-100: (x0, y0, x1, y1, boja)
SHAPES = [(22, 26, 78, 36, FG), (22, 45, 70, 55, FG), (22, 64, 56, 74, FG)]
DOT = (72, 69, 9, RED)  # centar x, y, poluprečnik


def pixel(x, y):
    cx, cy, r, col = DOT
    if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
        return col
    for x0, y0, x1, y1, col in SHAPES:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return col
    return BG


def png(size):
    rows = b"".join(
        b"\x00" + b"".join(bytes(pixel(x * 100 / size, y * 100 / size)) for x in range(size))
        for y in range(size)
    )
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="18" fill="#2b3a8c"/>'
       + "".join(f'<rect x="{a}" y="{b}" width="{c-a}" height="{d-b}" rx="3" fill="#fff"/>' for a, b, c, d, _ in SHAPES)
       + f'<circle cx="{DOT[0]}" cy="{DOT[1]}" r="{DOT[2]}" fill="#e6483c"/></svg>\n')
(ROOT / "assets" / "ikona.svg").write_text(svg, encoding="utf-8")
for s in (192, 512):
    (ROOT / "assets" / f"ikona-{s}.png").write_bytes(png(s))
