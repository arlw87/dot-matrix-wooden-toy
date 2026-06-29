#!/usr/bin/env python3
"""
Generate rocket animation preview images for the dot-matrix wooden toy.
Creates images/rocket/v1/, v2/, v3/ with frame PNGs and composite images.

Run from project root:  python3 generate_rocket_images.py
"""

import os
from PIL import Image, ImageDraw

# ── rendering constants ───────────────────────────────────────────────────────
CELL      = 32     # pixels per LED cell (individual frames)
COMP_CELL = 22     # pixels per LED cell (composite images)
GRID_W    = 16
GRID_H    = 16
GRID_COLOR = (12, 12, 18)
LABEL_H   = 52    # room for 3-line labels
TITLE_H   = 22

# ── palettes ──────────────────────────────────────────────────────────────────
# All colours chosen from hardware-tested visible set:
# strong: red, orange, amber, yellow, magnolia, green, lime, white
# avoid: grey, dark green, teal, navy, purple, dark red
# Nose/fins are magnolia or white (NOT grey — grey is invisible on the veneer)

V1 = {   # Classic night launch
    'sky':          (  4,   4,  14),   # near-black space
    'body':         ( 30, 155,  50),   # green body (ties to green button)
    'nose':         (210,  30,  20),   # red nose + fins
    'flame_outer':  (220,  85,  10),   # deep orange (closest to nozzle)
    'flame_mid':    (255, 145,  20),   # orange
    'flame_hot':    (255, 210,  40),   # yellow tip
}

V2 = {   # Brighter green, vivid flame
    'sky':          (  3,   6,  18),
    'body':         ( 35, 170,  55),   # green
    'nose':         (230,  25,  15),   # red nose + fins
    'flame_outer':  (230, 100,  15),   # orange
    'flame_mid':    (255, 165,  35),   # amber-orange
    'flame_hot':    (255, 228,  70),   # bright yellow
}

V3 = {   # High-energy — lime body, red-orange base flame
    'sky':          (  2,   4,  12),
    'body':         ( 55, 200,  70),   # lime green (punchier through veneer)
    'nose':         (220,  35,  20),   # red nose + fins
    'flame_outer':  (210,  60,  10),   # vivid red-orange base
    'flame_mid':    (240, 115,  15),   # orange
    'flame_hot':    (255, 222,  55),   # warm yellow tip
}

VERSIONS = [('v1', V1), ('v2', V2), ('v3', V3)]

# ── rocket pixel layout ───────────────────────────────────────────────────────
# Rocket centred on the 16-wide grid.  ry = nose tip row (negative = off-top).
#
#   Nose cone  — 3 rows, tapering: 2 → 4 → 6 wide   (nose colour)
#   Body       — 3 rows, 6 wide  (cols 5-10)          (green)
#   Fins       — 2 rows, fins extend beyond body:
#                  row 1: cols 3-4 + 5-10 + 11-12  = 10 wide
#                  row 2: cols 2-4 + 5-10 + 11-13  = 12 wide
#   Flame      — 1-3 rows below fins, from nozzle:
#                  outer: cols 6-9  (4 wide, orange)
#                  mid:   cols 6-9 or 5-10  (flickers)
#                  hot:   cols 7-8  (2 wide, yellow)

MAGNOLIA = (240, 240, 215)

def _rocket_pixels(palette, ry, flame_len=2, flame_seed=0):
    """Return list of (col, row, rgb). Clips nothing — caller filters out-of-bounds."""
    p = palette
    pxs = []

    # Nose cone — rows ry, ry+1, ry+2
    pxs += [(7, ry, p['nose']), (8, ry, p['nose'])]                      # tip: 2 wide
    for col in range(6, 10):
        pxs.append((col, ry + 1, p['nose']))                              # mid: 4 wide
    for col in range(5, 11):
        pxs.append((col, ry + 2, p['nose']))                              # base: 6 wide

    # Body — rows ry+3 to ry+6 (4 rows, 6 wide)
    for dy in (3, 4, 5, 6):
        for col in range(5, 11):
            pxs.append((col, ry + dy, p['body']))

    # Window — 2×2 magnolia square centred in the body (rows ry+4, ry+5; cols 7, 8)
    for dy in (4, 5):
        for col in (7, 8):
            pxs.append((col, ry + dy, MAGNOLIA))

    # Fins — rows ry+7 and ry+8
    # fin portions use nose colour; centre (body width) uses body colour
    for col in (3, 4):                                                     # left fin, row 7
        pxs.append((col, ry + 7, p['nose']))
    for col in range(5, 11):
        pxs.append((col, ry + 7, p['body']))                              # body centre
    for col in (11, 12):                                                   # right fin, row 7
        pxs.append((col, ry + 7, p['nose']))

    for col in (2, 3, 4):                                                  # left fin, row 8
        pxs.append((col, ry + 8, p['nose']))
    for col in range(5, 11):
        pxs.append((col, ry + 8, p['body']))                              # body centre
    for col in (11, 12, 13):                                               # right fin, row 8
        pxs.append((col, ry + 8, p['nose']))

    # Flame — starts at ry+9 (nozzle exit, 4 wide)
    for col in range(6, 10):
        pxs.append((col, ry + 9, p['flame_outer']))

    if flame_len >= 2:
        # Flame mid row — wide (6) or narrow (4) based on flicker seed
        cols = range(5, 11) if flame_seed % 2 == 0 else range(6, 10)
        for col in cols:
            pxs.append((col, ry + 10, p['flame_mid']))

    if flame_len >= 3:
        for col in (7, 8):
            pxs.append((col, ry + 11, p['flame_hot']))

    return pxs


# ── frame renderer ────────────────────────────────────────────────────────────
def _render(palette, ry, flame_len=2, flame_seed=0, cell=CELL):
    p = palette
    grid = [[p['sky']] * GRID_W for _ in range(GRID_H)]

    for col, row, colour in _rocket_pixels(palette, ry, flame_len, flame_seed):
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


# ── key-frame schedules ───────────────────────────────────────────────────────
# Rocket body spans ry (nose) to ry+7 (fin base), flame to ry+10.
# Total height ~11 rows — fills most of the 16-row display.
KEY_FRAMES = [
    # tag   ry  flame_len  seed  label
    ('000',  8,  1,  0, 'Entering\n(from bottom)'),   # fins at rows 15-16, flame off
    ('025',  3,  2,  0, '25%\n(rising)'),             # full rocket + flame visible
    ('050', -1,  2,  1, '50%\n(mid-flight)'),         # nose just off top, all visible
    ('075', -5,  3,  0, '75%\n(near top)'),           # fins+flame still in frame
    ('100',-13,  0,  0, 'Hold\n(rocket gone)'),       # fully exited
]

FLICKER_FRAMES = [
    # ry  flame_len  seed  label
    (3,  1,  0, 'Short\nflame'),
    (3,  2,  0, 'Mid\nflame\n(wide)'),
    (3,  2,  1, 'Mid\nflame\n(narrow)'),
    (3,  3,  0, 'Long\nflame'),
]


# ── composite builders ────────────────────────────────────────────────────────
def _add_text(draw, x, y, text, fill=(200, 210, 220)):
    for i, line in enumerate(text.split('\n')):
        draw.text((x, y + i * 13), line, fill=fill)


def _make_composite(palette, frames, title):
    n  = len(frames)
    cw = COMP_CELL * GRID_W
    ch = COMP_CELL * GRID_H
    W  = n * cw + (n - 1)
    H  = TITLE_H + ch + LABEL_H

    img  = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)
    draw.text((6, 4), title, fill=(190, 200, 215))

    for i, (ry, flame_len, flame_seed, label) in enumerate(frames):
        frame = _render(palette, ry, flame_len, flame_seed, cell=COMP_CELL)
        x_off = i * (cw + 1)
        img.paste(frame, (x_off, TITLE_H))
        _add_text(draw, x_off + 4, TITLE_H + ch + 4, label)

    return img


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    for vname, palette in VERSIONS:
        out_dir = os.path.join('images', 'rocket', vname)
        os.makedirs(out_dir, exist_ok=True)

        for tag, ry, flame_len, flame_seed, _ in KEY_FRAMES:
            img  = _render(palette, ry, flame_len, flame_seed, cell=CELL)
            path = os.path.join(out_dir, f'frame_{tag}.png')
            img.save(path)
            print(f'  saved {path}')

        path = os.path.join(out_dir, 'composite_path.png')
        frames = [(ry, fl, fs, lb) for _, ry, fl, fs, lb in KEY_FRAMES]
        _make_composite(palette, frames,
                        f'Rocket {vname} — animation path  '
                        f'(green body, red nose+fins, orange→yellow flame)'
                        ).save(path)
        print(f'  saved {path}')

        path = os.path.join(out_dir, 'composite_flicker.png')
        _make_composite(palette, FLICKER_FRAMES,
                        f'Rocket {vname} — flame flicker states at mid-flight (ry=4)'
                        ).save(path)
        print(f'  saved {path}')

    print('\nDone.')


if __name__ == '__main__':
    main()
