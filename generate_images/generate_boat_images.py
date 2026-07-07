#!/usr/bin/env python3
"""
Generate front-wheelhouse trawler preview images for the 16×16 LED matrix toy.
- Orange hull (4 rows), white wheelhouse at bow (left = direction of travel)
- Gold antenna above wheelhouse
- Blue water at bottom 2 rows (rows 14–15)
- Animation: drifts right to left with gentle 1-pixel bob

Run from project root:  python3 generate_boat_images.py
"""

import os
from PIL import Image, ImageDraw

CELL       = 32
COMP_CELL  = 22
GRID_W     = 16
GRID_H     = 16
GRID_COLOR = (12, 12, 18)
BG         = (0, 0, 0)

HULL_A     = (190,  55,  15)   # orange hull
HULL_B     = (140,  35,   8)   # dark orange lower hull / keel
CABIN      = (245, 245, 245)   # white wheelhouse
WINDOW     = ( 30,  50,  90)   # dark blue windows
DETAIL     = (220, 180,  90)   # gold antenna
WATER_SURF = ( 30,  90, 200)   # blue water surface (row 14)
WATER_DEEP = ( 10,  45, 130)   # dark blue water depth (row 15)

# ── water (always fixed rows 14–15) ───────────────────────────────────────────

def _water():
    out = []
    for col in range(GRID_W):
        out.append((col, 14, WATER_SURF))
        out.append((col, 15, WATER_DEEP))
    return out


# ── boat pixels ───────────────────────────────────────────────────────────────
# Base anchor: hull deck at row 10, hull left edge at col 2.
# Keel at row 13 sits adjacent to water surface at row 14.
#
# Boat faces LEFT (bow = left = direction of travel):
#
#   Antenna     col 4,  rows  3– 5
#   Wheelhouse  cols 2–6, rows  6– 9  (bow, left side)
#   Open deck   cols 7–13             (stern, right side, no structure)
#   Hull deck   cols 2–13, row 10
#   Hull body   cols 1–14, row 11
#   Hull body   cols 2–13, row 12
#   Keel        cols 3–12, row 13
#
# bx: horizontal shift (+ve = shifted right, -ve = left)
# by: vertical shift  (-1 = bob up one pixel, +1 = bob down into wave)

def _boat(bx=0, by=0):
    def p(col, row, colour):
        return (col + bx, row + by, colour)

    out = []

    # Antenna
    for row in range(3, 6):
        out.append(p(4, row, DETAIL))

    # Wheelhouse
    for row in range(6, 10):
        for col in range(2, 7):
            out.append(p(col, row, CABIN))
    for row in (7, 8):          # windows: 2 rows × 2 cols
        for col in (3, 4):
            out.append(p(col, row, WINDOW))

    # Hull
    for col in range(2, 14): out.append(p(col, 10, HULL_A))   # deck
    for col in range(1, 15): out.append(p(col, 11, HULL_A))   # hull body
    for col in range(2, 14): out.append(p(col, 12, HULL_B))   # hull body
    for col in range(3, 13): out.append(p(col, 13, HULL_B))   # keel

    return out


# ── rendering ─────────────────────────────────────────────────────────────────

def _render(bx=0, by=0, cell=CELL):
    grid = [[BG] * GRID_W for _ in range(GRID_H)]

    # Water first, then boat on top (boat can overlap water when bobbing down)
    for col, row, colour in _water():
        if 0 <= col < GRID_W and 0 <= row < GRID_H:
            grid[row][col] = colour
    for col, row, colour in _boat(bx, by):
        if 0 <= col < GRID_W and 0 <= row < GRID_H:
            grid[row][col] = colour

    W, H = cell * GRID_W, cell * GRID_H
    img  = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    for row in range(GRID_H):
        for col in range(GRID_W):
            x0, y0 = col * cell, row * cell
            draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1],
                           fill=grid[row][col])
    for i in range(GRID_W + 1):
        draw.line([(i * cell, 0), (i * cell, H)], fill=GRID_COLOR, width=1)
    for i in range(GRID_H + 1):
        draw.line([(0, i * cell), (W, i * cell)], fill=GRID_COLOR, width=1)
    return img


# ── animation path composite ──────────────────────────────────────────────────
# bx goes +11 → -2 (right to left).  by oscillates: 0, -1, 0, +1, 0.
# At by=+1 the keel dips into the water row — boat rides into a wave.

KEY_FRAMES = [
    (-13,  0, 'Entering\n(from left)'),
    ( -8, -1, '25%\n(bob up)'),
    ( -4,  0, '50%\n(wheelhouse entering)'),
    (  0, +1, '75%\n(bob down)'),
    ( +1,  0, 'Hold'),
]

LABEL_H = 48
TITLE_H = 22


def _make_composite():
    n  = len(KEY_FRAMES)
    cw = COMP_CELL * GRID_W
    ch = COMP_CELL * GRID_H
    W  = n * (cw + 1) - 1
    H  = TITLE_H + ch + LABEL_H

    img  = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)
    draw.text((6, 4),
              'Trawler — drift left→right with bob  (open bow enters first, wheelhouse enters last)',
              fill=(190, 200, 215))

    for i, (bx, by, label) in enumerate(KEY_FRAMES):
        frame = _render(bx, by, cell=COMP_CELL)
        x_off = i * (cw + 1)
        img.paste(frame, (x_off, TITLE_H))
        for j, line in enumerate(label.split('\n')):
            draw.text((x_off + 4, TITLE_H + ch + 6 + j * 14), line,
                      fill=(200, 210, 220))

    return img


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    out_dir = os.path.join('images', 'boat')
    os.makedirs(out_dir, exist_ok=True)

    # Full-size static design at base position
    path = os.path.join(out_dir, 'design.png')
    _render(bx=0, by=0).save(path)
    print(f'  saved {path}')

    # Animation path composite
    path = os.path.join(out_dir, 'composite.png')
    _make_composite().save(path)
    print(f'  saved {path}')

    print('\nDone.')


if __name__ == '__main__':
    main()
