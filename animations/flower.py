"""
Flower animation — 8 pink petals bloom outward from a yellow centre.

Uses V2 radial-oval geometry pre-computed at import time: pixel positions for
every bloom stage are stored in compact bytearrays so the animation loop only
does simple integer pixel draws with 4 set_pen calls per frame.
"""

import math
import time
from lib import display, sound

SOUND_FILE = "sounds/flower.wav"

# Palette — warm pink only (veneer safe)
_PETAL_COLOR  = (255,  90, 150)   # hot pink
_PETAL_TIP    = (255, 180, 205)   # pale pink tip (outer third of each petal)
_CENTER_COLOR = (255, 215,  40)   # yellow centre
_RING_COLOR   = (240, 150,  30)   # amber ring

# Full-bloom geometry
_N_PETALS  = 8
_CX = _CY  = 7.5
_PR_MAX    = 4.4    # petal oval centre distance from display centre
_MAJOR_MAX = 2.7    # petal half-length along radial axis
_MINOR_MAX = 1.25   # petal half-width along tangential axis
_CENTER_MAX = 2.5   # centre disc radius at full bloom

_N_FRAMES = 20      # pre-computed bloom stages (0 = bud, 20 = full bloom)


def _compute_frame(t):
    """Compute pixel positions for one bloom stage.

    Returns (petal_buf, tip_buf, centre_buf, ring_buf) — each a bytearray
    of [x0, y0, x1, y1, ...] pairs (values 0-15, fit in one byte each).
    """
    ease     = 1.0 - (1.0 - t) * (1.0 - t)
    pr       = 0.5  + (_PR_MAX    - 0.5)  * ease
    major    = 1.0  + (_MAJOR_MAX - 1.0)  * ease
    minor    = 0.8  + (_MINOR_MAX - 0.8)  * ease
    center_r = 2.0  + (_CENTER_MAX - 2.0) * ease

    tip_d2     = (pr + 0.4) ** 2
    angle_step = 2.0 * math.pi / _N_PETALS

    # 32-byte bitfield used as a 16x16 visited grid (avoids duplicate pixels)
    seen = bytearray(32)
    petal_pxs = []
    tip_pxs   = []

    for k in range(_N_PETALS):
        angle = k * angle_step
        ca, sa = math.cos(angle), math.sin(angle)
        pcx = _CX + pr * ca
        pcy = _CY + pr * sa
        search = int(major) + 2
        y_lo = max(0, int(pcy) - search)
        y_hi = min(15, int(pcy) + search)
        x_lo = max(0, int(pcx) - search)
        x_hi = min(15, int(pcx) + search)

        for y in range(y_lo, y_hi + 1):
            for x in range(x_lo, x_hi + 1):
                along = (x - pcx) * ca  + (y - pcy) * sa
                perp  = (x - pcx) * (-sa) + (y - pcy) * ca
                if (along / major) ** 2 + (perp / minor) ** 2 > 1.0:
                    continue
                # bitfield dedup
                bit_idx = y * 16 + x
                byte_i, bit_i = bit_idx >> 3, bit_idx & 7
                if seen[byte_i] & (1 << bit_i):
                    continue
                seen[byte_i] |= (1 << bit_i)

                d2 = (x - _CX) ** 2 + (y - _CY) ** 2
                if d2 > tip_d2:
                    tip_pxs.append(x)
                    tip_pxs.append(y)
                else:
                    petal_pxs.append(x)
                    petal_pxs.append(y)

    centre_pxs = []
    ring_pxs   = []
    r2       = center_r * center_r
    inner_r2 = (center_r * 0.68) ** 2
    search_c = int(center_r) + 1
    for y in range(max(0, int(_CY) - search_c), min(15, int(_CY) + search_c) + 1):
        for x in range(max(0, int(_CX) - search_c), min(15, int(_CX) + search_c) + 1):
            d2 = (x - _CX) ** 2 + (y - _CY) ** 2
            if d2 <= r2:
                if d2 <= inner_r2:
                    centre_pxs.append(x)
                    centre_pxs.append(y)
                else:
                    ring_pxs.append(x)
                    ring_pxs.append(y)

    return (bytearray(petal_pxs), bytearray(tip_pxs),
            bytearray(centre_pxs), bytearray(ring_pxs))


# Pre-compute all bloom stages once at import time.
_FRAMES = [_compute_frame(i / _N_FRAMES) for i in range(_N_FRAMES + 1)]


def _draw_frame(graphics, frame_idx):
    """Draw one pre-computed bloom frame. Only 4 set_pen calls."""
    petal_b, tip_b, centre_b, ring_b = _FRAMES[frame_idx]

    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    graphics.set_pen(graphics.create_pen(*_PETAL_COLOR))
    for i in range(0, len(petal_b), 2):
        display.pixel(graphics, petal_b[i], petal_b[i + 1])

    graphics.set_pen(graphics.create_pen(*_PETAL_TIP))
    for i in range(0, len(tip_b), 2):
        display.pixel(graphics, tip_b[i], tip_b[i + 1])

    graphics.set_pen(graphics.create_pen(*_CENTER_COLOR))
    for i in range(0, len(centre_b), 2):
        display.pixel(graphics, centre_b[i], centre_b[i + 1])

    graphics.set_pen(graphics.create_pen(*_RING_COLOR))
    for i in range(0, len(ring_b), 2):
        display.pixel(graphics, ring_b[i], ring_b[i + 1])


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

        t         = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        progress  = min(1.0, t / 5.0)
        frame_idx = min(_N_FRAMES, int(progress * _N_FRAMES))
        _draw_frame(graphics, frame_idx)
        su.update(graphics)
        time.sleep_ms(33)

    # Hold phase — full bloom for 5 seconds
    _draw_frame(graphics, _N_FRAMES)
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
