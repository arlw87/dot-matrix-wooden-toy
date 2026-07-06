"""
Flower animation — 8 pink petals bloom outward from a yellow centre.
Uses V2 radial-oval geometry: each petal is an ellipse whose centre sits
at distance PR_MAX from the display centre.  Outer pixels of each petal
are drawn in a pale-pink tip colour, inner pixels in hot pink.
"""

import time
import math
from lib import display, sound

SOUND_FILE = "sounds/flower.wav"

_CX, _CY = 7.5, 7.5

# Palette — warm pink only, no green
_PETAL_COLOR = (255,  90, 150)   # hot pink
_PETAL_TIP   = (255, 180, 205)   # pale pink tip (outer third of each petal)
_CENTER_COLOR = (255, 215,  40)  # yellow centre
_RING_COLOR   = (240, 150,  30)  # amber ring around centre

_NUM_PETALS = 8

# Full-bloom geometry (matches generate_flower_bloom.py V2)
_PR_MAX     = 4.4   # distance from display centre to each petal's oval centre
_MAJOR_MAX  = 2.7   # petal half-length along radial axis
_MINOR_MAX  = 1.25  # petal half-width along tangential axis
_CENTER_MAX = 2.5   # radius of centre disc at full bloom


def _draw_petal(graphics, angle, pr, major, minor):
    """Draw one radial oval petal. Tip pixels drawn in pale colour."""
    ca, sa = math.cos(angle), math.sin(angle)
    pcx, pcy = _CX + pr * ca, _CY + pr * sa

    search = major + 1
    y0 = int(pcy - search) - 1
    y1 = int(pcy + search) + 2
    x0 = int(pcx - search) - 1
    x1 = int(pcx + search) + 2

    for y in range(y0, y1):
        for x in range(x0, x1):
            if not (0 <= x < 16 and 0 <= y < 16):
                continue
            along = (x - pcx) * ca  + (y - pcy) * sa
            perp  = (x - pcx) * (-sa) + (y - pcy) * ca
            if (along / major) ** 2 + (perp / minor) ** 2 <= 1.0:
                dist = math.hypot(x - _CX, y - _CY)
                colour = _PETAL_TIP if dist > pr + 0.4 else _PETAL_COLOR
                graphics.set_pen(graphics.create_pen(*colour))
                display.pixel(graphics, x, y)


def _draw_centre(graphics, center_r):
    """Draw the filled centre disc with an amber ring."""
    r2 = center_r * center_r
    inner_r2 = (center_r * 0.68) ** 2
    for y in range(int(_CY - center_r) - 1, int(_CY + center_r) + 2):
        for x in range(int(_CX - center_r) - 1, int(_CX + center_r) + 2):
            if not (0 <= x < 16 and 0 <= y < 16):
                continue
            d2 = (x - _CX) ** 2 + (y - _CY) ** 2
            if d2 <= r2:
                colour = _CENTER_COLOR if d2 <= inner_r2 else _RING_COLOR
                graphics.set_pen(graphics.create_pen(*colour))
                display.pixel(graphics, x, y)


def _draw_flower(graphics, pr, major, minor, center_r):
    """Render one frame: petals first (behind), centre on top."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    angle_step = 2 * math.pi / _NUM_PETALS
    for i in range(_NUM_PETALS):
        _draw_petal(graphics, i * angle_step, pr, major, minor)

    _draw_centre(graphics, center_r)


def _bloom_state(t):
    """Return (pr, major, minor, center_r) for progress t in [0, 1], ease-out."""
    ease     = 1.0 - (1.0 - t) * (1.0 - t)
    pr       = 0.5  + (_PR_MAX    - 0.5)  * ease
    major    = 1.0  + (_MAJOR_MAX - 1.0)  * ease
    minor    = 0.8  + (_MINOR_MAX - 0.8)  * ease
    center_r = 2.0  + (_CENTER_MAX - 2.0) * ease
    return pr, major, minor, center_r


def play(su, graphics, check_interrupt=None):
    """
    Play the blooming flower animation.

    Returns None if completed normally, button name (str) if interrupted.
    """
    sound.play(su, SOUND_FILE)

    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            sound.stop(su)
            return interrupted_by

        t        = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        progress = t / 5.0
        _draw_flower(graphics, *_bloom_state(progress))
        su.update(graphics)
        time.sleep_ms(33)

    # Hold phase — full bloom for 5 seconds
    _draw_flower(graphics, *_bloom_state(1.0))
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
