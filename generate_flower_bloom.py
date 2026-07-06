#!/usr/bin/env python3
"""
Generate a bloom animation sequence for Flower V2 (8-petal orange).
Petals start tight at the centre and open outward to the full bloom.

Output: images/candidates/flower/bloom/
  frame_00.png .. frame_04.png  — individual keyframes
  bloom_composite.png           — all frames side by side

Run from project root:  python3 generate_flower_bloom.py
"""

import math
import os
from PIL import Image, ImageDraw

CELL       = 32
COMP_CELL  = 22
GRID_W     = 16
GRID_H     = 16
GRID_COLOR = (12, 12, 18)
BG         = (0, 0, 0)
LABEL_H    = 32
TITLE_H    = 22

# Flower V2 palette
PETAL  = (255, 120,  25)
TIP    = (225,  40,  45)
CENTER = (255, 225,  60)
RING   = (240, 150,  25)

# Full-bloom geometry (matches flower_v2)
PR_MAX    = 4.4
MAJOR_MAX = 2.7
MINOR_MAX = 1.25
N_PETALS  = 8


def _flower(pr, major, minor, center_r=2.5):
    """Build one bloom frame at the given petal geometry."""
    cx = cy = 7.5
    pixels = {}
    for k in range(N_PETALS):
        a = k * 2 * math.pi / N_PETALS
        ca, sa = math.cos(a), math.sin(a)
        pcx, pcy = cx + pr * ca, cy + pr * sa
        for col in range(GRID_W):
            for row in range(GRID_H):
                dx, dy = col - pcx, row - pcy
                rad = dx * ca + dy * sa
                tan = -dx * sa + dy * ca
                if (rad / major) ** 2 + (tan / minor) ** 2 <= 1.0:
                    dist = math.hypot(col - cx, row - cy)
                    pixels[(col, row)] = TIP if dist > pr + 0.4 else PETAL
    for col in range(GRID_W):
        for row in range(GRID_H):
            dist = math.hypot(col - cx, row - cy)
            if dist <= center_r:
                pixels[(col, row)] = CENTER if dist < center_r * 0.68 else RING
    return [(c, r, v) for (c, r), v in pixels.items()]


def _bloom_frame(t):
    """t in [0,1] — 0 = tight bud, 1 = full bloom."""
    ease = 1.0 - (1.0 - t) * (1.0 - t)          # ease-out
    pr    = 0.5 + (PR_MAX    - 0.5) * ease
    major = 1.0 + (MAJOR_MAX - 1.0) * ease
    minor = 0.8 + (MINOR_MAX - 0.8) * ease
    center_r = 2.0 + 0.5 * ease
    return _flower(pr, major, minor, center_r)


def _render(pixels, cell=CELL):
    grid = [[BG] * GRID_W for _ in range(GRID_H)]
    for col, row, colour in pixels:
        if 0 <= col < GRID_W and 0 <= row < GRID_H:
            grid[row][col] = colour
    W, H = cell * GRID_W, cell * GRID_H
    img  = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    for row in range(GRID_H):
        for col in range(GRID_W):
            x0, y0 = col * cell, row * cell
            draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=grid[row][col])
    for i in range(GRID_W + 1):
        draw.line([(i * cell, 0), (i * cell, H)], fill=GRID_COLOR, width=1)
    for i in range(GRID_H + 1):
        draw.line([(0, i * cell), (W, i * cell)], fill=GRID_COLOR, width=1)
    return img


def _composite(frames, title, cell=COMP_CELL):
    n  = len(frames)
    cw = cell * GRID_W
    ch = cell * GRID_H
    W  = n * (cw + 2) - 2
    H  = TITLE_H + ch + LABEL_H
    img  = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)
    draw.text((6, 4), title, fill=(190, 200, 215))
    for i, (pixels, label) in enumerate(frames):
        frame = _render(pixels, cell=cell)
        x_off = i * (cw + 2)
        img.paste(frame, (x_off, TITLE_H))
        draw.text((x_off + 4, TITLE_H + ch + 6), label, fill=(200, 210, 220))
    return img


def main():
    out_dir = os.path.join('images', 'candidates', 'flower', 'bloom')
    os.makedirs(out_dir, exist_ok=True)

    stops = [
        (0.00, 'Bud\n(0%)'),
        (0.25, 'Opening\n(25%)'),
        (0.50, 'Half\n(50%)'),
        (0.75, 'Nearly\n(75%)'),
        (1.00, 'Full bloom\n(hold)'),
    ]

    frames = []
    for i, (t, label) in enumerate(stops):
        pixels = _bloom_frame(t)
        _render(pixels).save(os.path.join(out_dir, f'frame_{i:02d}.png'))
        print(f'  saved frame_{i:02d}.png')
        frames.append((pixels, label))

    comp = _composite(frames, 'Flower V2 bloom — 8 orange petals open outward from centre')
    comp.save(os.path.join(out_dir, 'bloom_composite.png'))
    print('  saved bloom_composite.png')
    print('\nDone.')


if __name__ == '__main__':
    main()
