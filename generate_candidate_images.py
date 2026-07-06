#!/usr/bin/env python3
"""
Generate static design-review images for animation candidates:
  bird, duck, dinosaur, flower

Each produces 1–3 frames in images/candidates/<name>/.

Run from project root:  python3 generate_candidate_images.py
"""

import math
import os
from PIL import Image, ImageDraw

CELL        = 32
COMP_CELL   = 22
GRID_W      = 16
GRID_H      = 16
GRID_COLOR  = (12, 12, 18)
BG          = (0, 0, 0)
LABEL_H     = 36
TITLE_H     = 22


# ── shared renderer ──────────────────────────────────────────────────────────

def _render(pixels, bg=BG, cell=CELL):
    """pixels: list of (col, row, rgb_tuple). Returns a PIL Image."""
    grid = [[bg] * GRID_W for _ in range(GRID_H)]
    for col, row, colour in pixels:
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


def _composite(frames, title, cell=COMP_CELL):
    """frames: list of (pixel_list, label, bg). Returns a composite PIL Image."""
    n   = len(frames)
    cw  = cell * GRID_W
    ch  = cell * GRID_H
    W   = n * (cw + 2) - 2
    H   = TITLE_H + ch + LABEL_H
    img = Image.new('RGB', (W, H), (18, 18, 25))
    draw = ImageDraw.Draw(img)
    draw.text((6, 4), title, fill=(190, 200, 215))
    for i, (pixels, label, bg) in enumerate(frames):
        frame = _render(pixels, bg=bg, cell=cell)
        x_off = i * (cw + 2)
        img.paste(frame, (x_off, TITLE_H))
        draw.text((x_off + 4, TITLE_H + ch + 6), label, fill=(200, 210, 220))
    return img


def _parse(rows, legend):
    """Turn a list of 16 char-rows + legend dict into a pixel list."""
    out = []
    for row, line in enumerate(rows):
        for col, ch in enumerate(line):
            if ch in legend:
                out.append((col, row, legend[ch]))
    return out


# ── BIRD ─────────────────────────────────────────────────────────────────────
# Bird in flight seen head-on / from behind — the pose that actually reads as a
# bird at 16×16 (the shape a child draws). Symmetric body, two swept wings that
# flap: up-stroke → level glide → down-stroke.
# Warm palette only (orange / red / cream) for veneer visibility.

_BIRD_LEGEND = {
    'o': (235, 120,  25),   # body — orange
    'r': (205,  55,  35),   # lower body + tail — red
    'b': (255, 140,  35),   # wing — bright orange
    'w': (245, 238, 215),   # wing tip — cream
    'y': (255, 205,   5),   # beak (unused in head-on view)
}

# Up-stroke: wings raised in a high V.
_BIRD_UP = [
    "................",
    "................",
    "..ww........ww..",
    "...bw......wb...",
    "....bw.oo.wb....",
    ".....bwoowb.....",
    "......boob......",
    "......oooo......",
    "......orro......",
    ".......rr.......",
    ".......rr.......",
    ".......rr.......",
    "......r..r......",
    "................",
    "................",
    "................",
]

# Level: wings spread straight out — the glide frame.
_BIRD_LEVEL = [
    "................",
    "................",
    "................",
    "................",
    ".......oo.......",
    ".......oo.......",
    "...bbb.oo.bbb...",
    ".wwbbbboobbbbww.",
    "......orro......",
    ".......rr.......",
    ".......rr.......",
    ".......rr.......",
    "......r..r......",
    "................",
    "................",
    "................",
]

# Down-stroke: wings swept low in an inverted V.
_BIRD_DOWN = [
    "................",
    "................",
    "................",
    "................",
    ".......oo.......",
    ".......oo.......",
    ".......oo.......",
    "......boob......",
    ".....bbrrbb.....",
    "....bb.rr.bb....",
    "...bb..rr..bb...",
    "..ww...rr...ww..",
    "......r..r......",
    "................",
    "................",
    "................",
]


def generate_bird(out_dir):
    frames = [
        (_parse(_BIRD_UP,    _BIRD_LEGEND), 'Up-stroke',   BG),
        (_parse(_BIRD_LEVEL, _BIRD_LEGEND), 'Glide',       BG),
        (_parse(_BIRD_DOWN,  _BIRD_LEGEND), 'Down-stroke', BG),
    ]
    for label, (pixels, lbl, bg) in zip(['up', 'level', 'down'], frames):
        _render(pixels, bg=bg).save(os.path.join(out_dir, f'bird_{label}.png'))
        print(f'  saved bird_{label}.png')
    comp = _composite(frames, 'Bird — head-on flight, warm palette, flap cycle')
    comp.save(os.path.join(out_dir, 'bird_composite.png'))
    print('  saved bird_composite.png')


# ── DUCK ─────────────────────────────────────────────────────────────────────
# Round amber-orange body, cream chest, orange bill.
# Swimming right; two frames: calm / splash-wing raised.

_DUCK_BODY   = (230, 140, 20)
_DUCK_CHEST  = (245, 210, 120)
_DUCK_BILL   = (255, 175,  30)
_DUCK_WING   = (190,  95,  10)
_DUCK_EYE    = ( 15,  15,  15)
_DUCK_WATER  = (  0, 180, 200)   # aqua — hardware-approved
_DUCK_WAKE   = (  0, 145, 165)   # slightly darker aqua


def _duck_base():
    p = []
    # body — large round oval
    for col in range(5, 13): p.append((col, 7, _DUCK_BODY))
    for col in range(3, 14): p.append((col, 8, _DUCK_BODY))
    for col in range(3, 14): p.append((col, 9, _DUCK_BODY))
    for col in range(4, 13): p.append((col, 10, _DUCK_BODY))
    for col in range(5, 12): p.append((col, 11, _DUCK_BODY))
    # chest highlight
    for col in range(11, 14): p.append((col, 8, _DUCK_CHEST))
    for col in range(11, 14): p.append((col, 9, _DUCK_CHEST))
    for col in range(10, 13): p.append((col, 10, _DUCK_CHEST))
    # head
    for col in range(8, 13):  p.append((col, 5, _DUCK_BODY))
    for col in range(7, 13):  p.append((col, 6, _DUCK_BODY))
    for col in range(8, 12):  p.append((col, 7, _DUCK_BODY))
    p.append((11, 5, _DUCK_EYE))
    # bill (facing right)
    p.append((13, 6, _DUCK_BILL))
    p.append((14, 6, _DUCK_BILL))
    p.append((13, 7, _DUCK_BILL))
    # tail (left side, slightly up)
    p.append((2, 7, _DUCK_WING))
    p.append((2, 8, _DUCK_WING))
    p.append((1, 8, _DUCK_WING))
    p.append((2, 9, _DUCK_WING))
    # water surface
    for col in range(0, 16): p.append((col, 12, _DUCK_WATER))
    for col in range(0, 16): p.append((col, 13, _DUCK_WATER))
    for col in range(0, 16): p.append((col, 14, _DUCK_WAKE))
    for col in range(0, 16): p.append((col, 15, _DUCK_WAKE))
    # wake ripple marks
    for col in (1, 2, 4): p.append((col, 12, _DUCK_WAKE))
    return p


def _duck_wing_raised():
    p = _duck_base()
    # raised wing
    for col in range(5, 10):  p.append((col, 4, _DUCK_WING))
    for col in range(4, 11):  p.append((col, 5, _DUCK_WING))
    for col in range(4, 11):  p.append((col, 6, _DUCK_WING))
    for col in range(5, 10):  p.append((col, 7, _DUCK_WING))
    # splash dots on water
    for col in (1, 3, 5): p.append((col, 11, _DUCK_WATER))
    return p


def generate_duck(out_dir):
    frames = [
        (_duck_base(),         'Calm swim',   BG),
        (_duck_wing_raised(),  'Wing raised',  BG),
    ]
    for label, (pixels, lbl, bg) in zip(['calm', 'wing'], frames):
        _render(pixels, bg=bg).save(os.path.join(out_dir, f'duck_{label}.png'))
        print(f'  saved duck_{label}.png')
    comp = _composite(frames, 'Duck — amber body, aqua water, swimming right')
    comp.save(os.path.join(out_dir, 'duck_composite.png'))
    print('  saved duck_composite.png')


# ── DINOSAUR (T-Rex) ─────────────────────────────────────────────────────────
# Orange-red body — NO green (veneer). Dark maroon shadow.
# Facing right. Two frames: standing / mid-stomp.

_DINO_BODY   = (210,  75, 15)
_DINO_BELLY  = (235, 145, 55)
_DINO_DARK   = (150,  45,  8)
_DINO_EYE    = ( 15,  15, 15)
_DINO_TEETH  = (240, 235, 210)   # magnolia off-white
_DINO_CLAW   = (240, 235, 210)


def _dino_pixels(stomp=False):
    """stomp=True lifts right leg."""
    p = []

    # ── head ──────────────────────────────────────────────────────────────
    for col in range(9, 15):  p.append((col, 1, _DINO_BODY))   # top of skull
    for col in range(9, 15):  p.append((col, 2, _DINO_BODY))   # skull
    for col in range(8, 15):  p.append((col, 3, _DINO_BODY))   # jaw top
    for col in range(9, 16):  p.append((col, 4, _DINO_BODY))   # jaw
    # teeth row — small magnolia pixels on bottom jaw
    for col in (9, 11, 13):  p.append((col, 5, _DINO_TEETH))
    p.append((14, 3, _DINO_TEETH))   # tooth on upper jaw tip
    # eye
    p.append((12, 2, _DINO_EYE))

    # ── neck ──────────────────────────────────────────────────────────────
    for col in range(6, 10):  p.append((col, 2, _DINO_BODY))
    for col in range(5, 9):   p.append((col, 3, _DINO_BODY))
    for col in range(5, 9):   p.append((col, 4, _DINO_BODY))

    # ── body ──────────────────────────────────────────────────────────────
    for col in range(3, 11):  p.append((col, 5, _DINO_BODY))
    for col in range(2, 11):  p.append((col, 6, _DINO_BODY))
    for col in range(2, 11):  p.append((col, 7, _DINO_BODY))
    for col in range(2, 10):  p.append((col, 8, _DINO_BODY))
    for col in range(3, 10):  p.append((col, 9, _DINO_BODY))
    for col in range(4, 9):   p.append((col, 10, _DINO_BODY))
    # belly highlight
    for col in range(7, 10):  p.append((col, 6, _DINO_BELLY))
    for col in range(7, 10):  p.append((col, 7, _DINO_BELLY))
    for col in range(7, 9):   p.append((col, 8, _DINO_BELLY))

    # ── tiny arms ─────────────────────────────────────────────────────────
    p.append((10, 5, _DINO_DARK))
    p.append((11, 5, _DINO_DARK))
    p.append((11, 6, _DINO_CLAW))

    # ── tail (extends left, tapering) ──────────────────────────────────────
    for col in range(0, 3):   p.append((col, 7, _DINO_BODY))
    for col in range(0, 2):   p.append((col, 8, _DINO_DARK))
    p.append((0, 9, _DINO_DARK))

    # ── legs ──────────────────────────────────────────────────────────────
    if not stomp:
        # standing — both legs down
        for row in range(11, 14): p.append((5, row, _DINO_BODY))
        for row in range(11, 14): p.append((6, row, _DINO_DARK))
        for row in range(11, 14): p.append((8, row, _DINO_BODY))
        for row in range(11, 14): p.append((9, row, _DINO_DARK))
        # feet
        for col in (4, 5, 6):    p.append((col, 14, _DINO_BODY))
        for col in (8, 9, 10):   p.append((col, 14, _DINO_BODY))
        # claws
        p.append((4, 15, _DINO_CLAW))
        p.append((6, 15, _DINO_CLAW))
        p.append((8, 15, _DINO_CLAW))
        p.append((10, 15, _DINO_CLAW))
    else:
        # stomp — left leg planted, right leg raised forward
        for row in range(11, 15): p.append((5, row, _DINO_BODY))
        for row in range(11, 15): p.append((6, row, _DINO_DARK))
        # foot on ground
        for col in (4, 5, 6):    p.append((col, 15, _DINO_BODY))
        p.append((4, 15, _DINO_CLAW))
        p.append((6, 15, _DINO_CLAW))
        # raised right leg — bent forward
        p.append((8, 10, _DINO_BODY))
        p.append((9, 10, _DINO_BODY))
        p.append((9, 9, _DINO_DARK))
        p.append((10, 9, _DINO_DARK))
        p.append((11, 9, _DINO_BODY))
        p.append((11, 10, _DINO_BODY))
        p.append((12, 10, _DINO_CLAW))

    return p


def generate_dino(out_dir):
    frames = [
        (_dino_pixels(stomp=False), 'Standing',    BG),
        (_dino_pixels(stomp=True),  'Mid-stomp',   BG),
    ]
    for label, (pixels, lbl, bg) in zip(['stand', 'stomp'], frames):
        _render(pixels, bg=bg).save(os.path.join(out_dir, f'dino_{label}.png'))
        print(f'  saved dino_{label}.png')
    comp = _composite(frames, 'Dinosaur (T-Rex) — orange-red, no green, stomp animation')
    comp.save(os.path.join(out_dir, 'dino_composite.png'))
    print('  saved dino_composite.png')


# ── FLOWER ───────────────────────────────────────────────────────────────────
# Fully-open bloom. Each petal is a clean radial oval so the petals read as
# distinct lobes (not a solid disc). Warm colours only — veneer safe.

def _flower_bloom(n_petals, petal, tip, center, ring,
                  pr=4.2, major=2.7, minor=1.5, phase=0.0):
    """
    n_petals ovals arranged around centre (7.5, 7.5).
      pr    — distance from centre to each petal's centre
      major — petal half-length (radial)
      minor — petal half-width (tangential)
    Outer third of each petal takes the tip colour.
    """
    cx = cy = 7.5
    pixels = {}
    for k in range(n_petals):
        a = phase + k * 2 * math.pi / n_petals
        ca, sa = math.cos(a), math.sin(a)
        pcx, pcy = cx + pr * ca, cy + pr * sa
        for col in range(GRID_W):
            for row in range(GRID_H):
                dx, dy = col - pcx, row - pcy
                rad = dx * ca + dy * sa            # along petal
                tan = -dx * sa + dy * ca           # across petal
                if (rad / major) ** 2 + (tan / minor) ** 2 <= 1.0:
                    dist = math.hypot(col - cx, row - cy)
                    pixels[(col, row)] = tip if dist > pr + 0.4 else petal
    # centre disc drawn last, on top
    for col in range(GRID_W):
        for row in range(GRID_H):
            dist = math.hypot(col - cx, row - cy)
            if dist <= 2.5:
                pixels[(col, row)] = center if dist < 1.7 else ring
    return [(c, r, v) for (c, r), v in pixels.items()]


def _flower_v1():
    """6-petal pink daisy, yellow eye."""
    return _flower_bloom(6,
                         petal=(255,  90, 150),
                         tip=(255, 180, 205),
                         center=(255, 215,  40),
                         ring=(240, 150,  30),
                         pr=4.2, major=2.8, minor=1.6)


def _flower_v2():
    """8-petal orange/red — bold, most veneer-safe."""
    return _flower_bloom(8,
                         petal=(255, 120,  25),
                         tip=(225,  40,  45),
                         center=(255, 225,  60),
                         ring=(240, 150,  25),
                         pr=4.4, major=2.7, minor=1.25)


def _flower_v3():
    """5-petal red bloom, pink tips — fuller petals."""
    return _flower_bloom(5,
                         petal=(220,  40,  50),
                         tip=(255, 175, 200),
                         center=(255, 205,  40),
                         ring=(210,  90,  20),
                         pr=4.0, major=2.9, minor=1.9, phase=-math.pi / 2)


def generate_flower(out_dir):
    frames = [
        (_flower_v1(), '6-petal pink',   BG),
        (_flower_v2(), '8-petal orange', BG),
        (_flower_v3(), '5-petal red',    BG),
    ]
    for label, (pixels, lbl, bg) in zip(['v1_pink', 'v2_orange', 'v3_red'], frames):
        _render(pixels, bg=bg).save(os.path.join(out_dir, f'flower_{label}.png'))
        print(f'  saved flower_{label}.png')
    comp = _composite(frames, 'Flower — clean radial petals, warm colours (pink / orange / red)')
    comp.save(os.path.join(out_dir, 'flower_composite.png'))
    print('  saved flower_composite.png')


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    base = os.path.join('images', 'candidates')
    for name, fn in [('bird', generate_bird), ('duck', generate_duck),
                     ('dino', generate_dino), ('flower', generate_flower)]:
        d = os.path.join(base, name)
        os.makedirs(d, exist_ok=True)
        print(f'\n{name.upper()}:')
        fn(d)
    print('\nDone.')


if __name__ == '__main__':
    main()
