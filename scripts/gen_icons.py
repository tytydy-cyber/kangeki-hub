#!/usr/bin/env python3
"""PWA用アイコンPNGを生成する（Python標準ライブラリのみ）。

紅テント（アングラ・テント芝居）をモチーフにした、深紅背景＋クリーム色のテント三角形。
出力: site/assets/icons/ 以下に各サイズのPNG。

使い方: python3 scripts/gen_icons.py
"""

import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site" / "assets" / "icons"

BG = (158, 43, 43, 255)       # 深紅（紅テント）
TENT = (245, 240, 230, 255)   # クリーム
DOOR = (120, 26, 26, 255)     # テントの入口（暗い赤）


def write_png(path, size, pixels):
    def chunk(typ, data):
        return (
            struct.pack(">I", len(data))
            + typ
            + data
            + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8bit RGBA
    raw = bytearray()
    row = size * 4
    for y in range(size):
        raw.append(0)  # filter: none
        raw += pixels[y * row : (y + 1) * row]
    idat = zlib.compress(bytes(raw), 9)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    )


def sign(ax, ay, bx, by, cx, cy):
    return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)


def in_triangle(px, py, a, b, c):
    d1 = sign(px, py, *a, *b)
    d2 = sign(px, py, *b, *c)
    d3 = sign(px, py, *c, *a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def render(size, safe):
    """safe: 端の余白比（0〜0.5）。maskableは大きめに取る。"""
    s = size
    apex = (s * 0.5, s * safe)
    base_y = s * (1 - safe)
    half = (0.5 - safe) * s
    bl = (s * 0.5 - half, base_y)
    br = (s * 0.5 + half, base_y)
    # 入口（テント下部中央の暗い赤の縦長）
    door_w = s * 0.10
    door_x0, door_x1 = s * 0.5 - door_w / 2, s * 0.5 + door_w / 2
    door_y0 = base_y - (0.5 - safe) * s * 0.55

    px = bytearray(s * s * 4)
    for y in range(s):
        cy = y + 0.5
        for x in range(s):
            cx = x + 0.5
            color = BG
            if in_triangle(cx, cy, apex, bl, br):
                color = TENT
                if door_x0 <= cx <= door_x1 and door_y0 <= cy <= base_y:
                    color = DOOR
            i = (y * s + x) * 4
            px[i : i + 4] = bytes(color)
    return px


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 通常アイコン（余白控えめ）
    for size in (192, 512):
        write_png(OUT / f"icon-{size}.png", size, render(size, 0.20))
    # maskable（Androidのアダプティブアイコン用に安全領域を広めに）
    write_png(OUT / "icon-maskable-512.png", 512, render(512, 0.30))
    # apple-touch / favicon（あれば体裁が整う）
    write_png(OUT / "apple-touch-icon.png", 180, render(180, 0.20))
    write_png(OUT / "favicon-32.png", 32, render(32, 0.16))
    for p in sorted(OUT.glob("*.png")):
        print(p.relative_to(OUT.parent.parent), p.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
