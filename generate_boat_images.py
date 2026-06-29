#!/usr/bin/env python3
"""
Generate boat animation preview images for the dot-matrix wooden toy.
Creates images/boat/v1/, v2/, v3/ with frame PNGs and composite images.

Run from project root:  python3 generate_boat_images.py
"""

import math
import os
from PIL import Image, ImageDraw

# ── rendering constants ───────────────────────────────────────────────────────
CELL      = 32     # pixels per LED cell (individual frames)
COMP_CELL = 22     # pixels per LED cell (composite images)
GRID_W    = 16
GRID_H    = 16
GRID_COLOR = (12, 12, 18)

# ── animation constants ───────────────────────────────────────────────────────
WATERLINE = 10     # row where hull base sits at rest
WATER_TOP = 11     # first fully-water row

# ── palettes ──────────────────────────────────────────────────────────────────
V1 = {   # Classic daytime, bright sky
    'sky':         (100, 165, 215),
    'water_deep':  ( 10,  40, 120),
    'water_mid':   ( 20,  75, 175),
    'water_crest': ( 55, 140, 225),
    'hull':        ( 20,  55, 155),
    'hull_top':    ( 35,  85, 200),
    'sail':        (238, 243, 255),
    'mast':        (195, 155,  80),
    'wake':        (155, 210, 250),
}

V2 = {   # Twilight — darker sky, muted colours
    'sky':         ( 35,  50, 105),
    'water_deep':  (  5,  20,  75),
    'water_mid':   ( 12,  48, 130),
    'water_crest': ( 35,  95, 180),
    'hull':        ( 15,  35, 110),
    'hull_top':    ( 25,  60, 150),
    'sail':        (205, 215, 240),
    'mast':        (140, 105,  55),
    'wake':        ( 90, 150, 200),
}

V3 = {   # High-contrast, veneer-friendly (no green, deep blues, bright whites)
    'sky':         ( 60, 120, 195),
    'water_deep':  (  0,  25, 100),
    'water_mid':   (  8,  55, 160),
    'water_crest': ( 45, 125, 230),
    'hull':        (  0,  35, 150),
    'hull_top':    ( 15,  65, 190),
    'sail':        (255, 255, 255),
    'mast':        (220, 180,  95),
    'wake':        (195, 230, 255),
}

VERSIONS = [
    ('v1', V1, 'left'),    # drifts left (enters from right)
    ('v2', V2, 'right'),   # drifts right (enters from left)
    ('v3', V3, 'left'),
]


# ── boat pixel layout ─────────────────────────────────────────────────────────
def _boat_pixels(palette, direction='left'):
    """
    (dx, dy, colour) relative to anchor (bx, wy).
    dy=0  hull base row (=WATERLINE at rest)
    dy<0  above hull base (negative = up)
    direction: 'left' = sailing left, wake trails right;
               'right' = sailing right, wake trails left.
    """
    p = palette
    pxs = []
    # Hull base (dy=0): 8 wide, dx=0..7
    for dx in range(8):
        pxs.append((dx, 0, p['hull']))
    # Hull top (dy=-1): 6 wide, dx=1..6
    for dx in range(1, 7):
        pxs.append((dx, -1, p['hull_top']))
    # Mast (dx=3): dy=-2..-5
    for dy in range(-2, -6, -1):
        pxs.append((3, dy, p['mast']))
    # Sail (right of mast): widest in middle, tapers top and bottom
    # dy=-2  dx=4,5
    pxs += [(4, -2, p['sail']), (5, -2, p['sail'])]
    # dy=-3  dx=4,5,6
    pxs += [(4, -3, p['sail']), (5, -3, p['sail']), (6, -3, p['sail'])]
    # dy=-4  dx=4,5
    pxs += [(4, -4, p['sail']), (5, -4, p['sail'])]
    # dy=-5  dx=4  (tip)
    pxs.append((4, -5, p['sail']))
    # Wake (2 pixels trailing behind)
    if direction == 'left':   # moving left → wake on the right
        pxs += [(8, 0, p['wake']), (9, 0, p['wake'])]
    else:                      # moving right → wake on the left
        pxs += [(-1, 0, p['wake']), (-2, 0, p['wake'])]
    return pxs


# ── rendering helpers ─────────────────────────────────────────────────────────
def _water_colour(col, row, wave_phase, palette):
    """Return RGB for a water pixel at (col, row) given wave_phase."""
    p   = palette
    wav = 0.5 + 0.5 * math.sin(col * 1.3 + wave_phase)
    if row == WATER_TOP:
        lo, hi = p['water_mid'], p['water_crest']
        return tuple(int(lo[i] + wav * (hi[i] - lo[i])) for i in range(3))
    elif row == WATER_TOP + 1:
        lo, hi = p['water_deep'], p['water_mid']
        return tuple(int(lo[i] + 0.4 * (hi[i] - lo[i])) for i in range(3))
    else:
        return p['water_deep']


def _render(palette, bx, wy, wave_phase, direction, cell=CELL):
    """Render one 16×16 frame into a PIL Image."""
    W, H = cell * GRID_W, cell * GRID_H
    grid  = [[palette['sky']] * GRID_W for _ in range(GRID_H)]

    # Water band
    for row in range(WATER_TOP, GRID_H):
        for col in range(GRID_W):
            grid[row][col] = _water_colour(col, row, wave_phase, palette)

    # Boat pixels
    for dx, dy, colour in _boat_pixels(palette, direction):
        px, py = bx + dx, wy + dy
        if 0 <= px < GRID_W and 0 <= py < GRID_H:
            grid[py][px] = colour

    # Blit to image
    img  = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(img)
    for row in range(GRID_H):
        for col in range(GRID_W):
            x0, y0 = col * cell, row * cell
            draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1],
                           fill=grid[row][col])

    # Grid lines
    for i in range(GRID_W + 1):
        draw.line([(i * cell, 0), (i * cell, H)], fill=GRID_COLOR, width=1)
    for i in range(GRID_H + 1):
        draw.line([(0, i * cell), (W, i * cell)], fill=GRID_COLOR, width=1)

    return img


# ── key-frame schedules ───────────────────────────────────────────────────────
def _key_frames(direction):
    """
    Return list of (tag, bx, bob_offset, wave_phase, label) for composite_path.
    bob_offset: 0 = at WATERLINE, -1 = one pixel above (cresting wave).
    """
    # Drift left: bx goes 12 → 0  over the animation; hold at bx=0
    # Drift right: bx goes 0 → 12 over the animation; hold at bx=12
    if direction == 'left':
        positions = [
            ('000', 12, 0,  0.00 * math.pi, 'Entering\n(from right)'),
            ('025',  9, -1, 0.50 * math.pi, '25 %\n(bob up)'),
            ('050',  6, 0,  1.00 * math.pi, '50 %\n(bob down)'),
            ('075',  3, -1, 1.50 * math.pi, '75 %\n(bob up)'),
            ('100',  0, 0,  2.00 * math.pi, 'Hold\n(centre-left)'),
        ]
    else:
        positions = [
            ('000', -1, 0,  0.00 * math.pi, 'Entering\n(from left)'),
            ('025',  2, -1, 0.50 * math.pi, '25 %\n(bob up)'),
            ('050',  5, 0,  1.00 * math.pi, '50 %\n(bob down)'),
            ('075',  8, -1, 1.50 * math.pi, '75 %\n(bob up)'),
            ('100', 11, 0,  2.00 * math.pi, 'Hold\n(centre-right)'),
        ]
    return [(tag, bx, WATERLINE + bob, phase, label)
            for tag, bx, bob, phase, label in positions]


def _wave_frames(direction, hold_bx):
    """4 frames of wave cycle at hold position for composite_wave."""
    phases = [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]
    labels = ['Wave state A', 'Wave state B', 'Wave state C', 'Wave state D']
    frames = []
    for ph, lb in zip(phases, labels):
        bob = WATERLINE + (-1 if math.sin(ph) > 0 else 0)
        frames.append((hold_bx, bob, ph, lb))
    return frames


# ── composite builders ────────────────────────────────────────────────────────
LABEL_H = 36   # height in pixels for label strip at bottom
TITLE_H = 22   # height for title strip at top

def _add_text(draw, x, y, text, fill=(200, 210, 220), size=11):
    """Draw multi-line text centred at x, starting at y."""
    for i, line in enumerate(text.split('\n')):
        draw.text((x, y + i * (size + 2)), line, fill=fill)


def _make_composite_path(palette, direction, version_name):
    frames = _key_frames(direction)
    n      = len(frames)
    cw     = COMP_CELL * GRID_W   # per-frame canvas width
    ch     = COMP_CELL * GRID_H
    W      = n * cw + (n - 1)     # 1px dividers
    H      = TITLE_H + ch + LABEL_H

    img  = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)

    title = (f'Boat {version_name} — animation path  '
             f'({"drift left" if direction == "left" else "drift right"},'
             f' blue hull, white sail, animated waves)')
    draw.text((6, 4), title, fill=(190, 200, 215))

    for i, (tag, bx, wy, phase, label) in enumerate(frames):
        frame = _render(palette, bx, wy, phase, direction, cell=COMP_CELL)
        x_off = i * (cw + 1)
        img.paste(frame, (x_off, TITLE_H))
        _add_text(draw, x_off + 4, TITLE_H + ch + 4, label)

    return img


def _make_composite_wave(palette, direction, version_name):
    """4-panel wave-cycle composite at hold position."""
    hold_bx = 0 if direction == 'left' else 11
    frames  = _wave_frames(direction, hold_bx)
    n       = len(frames)
    cw      = COMP_CELL * GRID_W
    ch      = COMP_CELL * GRID_H
    W       = n * cw + (n - 1)
    H       = TITLE_H + ch + LABEL_H

    img  = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)
    draw.text((6, 4), f'Boat {version_name} — wave animation cycle at hold position',
              fill=(190, 200, 215))

    for i, (bx, wy, phase, label) in enumerate(frames):
        frame = _render(palette, bx, wy, phase, direction, cell=COMP_CELL)
        x_off = i * (cw + 1)
        img.paste(frame, (x_off, TITLE_H))
        _add_text(draw, x_off + 4, TITLE_H + ch + 4, label)

    return img


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    for vname, palette, direction in VERSIONS:
        out_dir = os.path.join('images', 'boat', vname)
        os.makedirs(out_dir, exist_ok=True)

        # Individual key frames (full-size)
        for tag, bx, wy, phase, _ in _key_frames(direction):
            img  = _render(palette, bx, wy, phase, direction, cell=CELL)
            path = os.path.join(out_dir, f'frame_{tag}.png')
            img.save(path)
            print(f'  saved {path}')

        # Composite path
        path = os.path.join(out_dir, 'composite_path.png')
        _make_composite_path(palette, direction, vname).save(path)
        print(f'  saved {path}')

        # Composite wave
        path = os.path.join(out_dir, 'composite_wave.png')
        _make_composite_wave(palette, direction, vname).save(path)
        print(f'  saved {path}')

    print('\nDone.')


if __name__ == '__main__':
    main()
