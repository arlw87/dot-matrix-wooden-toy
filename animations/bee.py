"""
Bee animation — a large bee rises from below the display, oscillates up and
down twice, then holds in the centre with wings still flickering.
sounds/bee.wav plays if present; runs silently if the file is absent.

Bee is 12 wide x 8 tall, centred horizontally (anchor bx=2 on 16-wide grid).
Horizontal yellow/black stripes with white wings on left and right sides.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/bee.wav"

# ── palette ───────────────────────────────────────────────────────────────────
_YELLOW = (255, 195,   0)
_DARK   = ( 65,  65,  65)   # bee body black — visible against dark background
_WHITE  = (235, 240, 255)   # wings

# ── body pixels: (dx, dy, colour) relative to anchor (bx, by) ────────────────
_BODY = [
    # Antennas
    (4, 0, _DARK),  (7, 0, _DARK),
    # Head (yellow)
    (3, 1, _YELLOW), (4, 1, _YELLOW), (5, 1, _YELLOW),
    (6, 1, _YELLOW), (7, 1, _YELLOW), (8, 1, _YELLOW),
    # Stripe 1 — dark
    (3, 2, _DARK),  (4, 2, _DARK),  (5, 2, _DARK),
    (6, 2, _DARK),  (7, 2, _DARK),  (8, 2, _DARK),
    # Stripe 2 — yellow
    (3, 3, _YELLOW), (4, 3, _YELLOW), (5, 3, _YELLOW),
    (6, 3, _YELLOW), (7, 3, _YELLOW), (8, 3, _YELLOW),
    # Stripe 3 — dark
    (3, 4, _DARK),  (4, 4, _DARK),  (5, 4, _DARK),
    (6, 4, _DARK),  (7, 4, _DARK),  (8, 4, _DARK),
    # Stripe 4 — yellow
    (3, 5, _YELLOW), (4, 5, _YELLOW), (5, 5, _YELLOW),
    (6, 5, _YELLOW), (7, 5, _YELLOW), (8, 5, _YELLOW),
    # Tail — dark
    (3, 6, _DARK),  (4, 6, _DARK),  (5, 6, _DARK),
    (6, 6, _DARK),  (7, 6, _DARK),  (8, 6, _DARK),
    # Stinger
    (5, 7, _YELLOW), (6, 7, _YELLOW),
]

# ── fixed layout values ───────────────────────────────────────────────────────
_BX        = 2   # horizontal anchor — centres 12-wide bee on 16-wide grid
_BY_CENTRE = 4   # vertical anchor at rest / hold position
_BY_AMP    = 3   # oscillation amplitude in pixels

_ANIM_MS   = 5000
_HOLD_MS   = 5000


def _wings(shift):
    """
    Return wing pixels for one frame.
    shift=0 (upstroke): wings at rows 2–3.
    shift=1 (downstroke): wings at rows 3–4.
    2-row shift gives a clear flicker at 16×16 resolution.
    """
    wy = 2 + shift
    return [
        (0,  wy,     _WHITE), (1,  wy,     _WHITE),
        (0,  wy + 1, _WHITE), (1,  wy + 1, _WHITE),
        (10, wy,     _WHITE), (11, wy,     _WHITE),
        (10, wy + 1, _WHITE), (11, wy + 1, _WHITE),
    ]


def _bee_y(t, amp):
    """
    Vertical anchor position at normalised time t (0.0–1.0).

    0.00–0.18  Entry: rises from off-screen (by=16) to centre (by=_BY_CENTRE).
    0.18–0.85  Oscillation: 2 full up/down cycles around centre; starts upward.
    0.85–1.00  Hold: rests at centre.
    """
    if t <= 0.18:
        progress = t / 0.18
        return int(round(16 - progress * (16 - _BY_CENTRE)))
    elif t <= 0.85:
        phase = (t - 0.18) / (0.85 - 0.18)
        return int(round(_BY_CENTRE - amp * math.sin(phase * 4 * math.pi)))
    else:
        return _BY_CENTRE


def _draw_bee(graphics, bx, by, wing_shift):
    """Clear display and draw bee at (bx, by) with given wing state."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    for dx, dy, (r, g, b) in _BODY + _wings(wing_shift):
        px, py = bx + dx, by + dy
        if 0 <= px < 16 and 0 <= py < 16:
            graphics.set_pen(graphics.create_pen(r, g, b))
            display.pixel(graphics, px, py)


def play(su, graphics, check_interrupt=None):
    """
    Play the bee animation.
    Returns None if completed normally, or the button name (str) if interrupted.
    """
    _sound_ok = False
    try:
        sound.play(su, SOUND_FILE)
        _sound_ok = True
    except OSError:
        pass

    # Per-play variation: amplitude only (keeps loop count deterministic)
    amp = _BY_AMP + random.uniform(-0.5, 0.5)

    start = time.ticks_ms()
    wing_shift = 0

    # ── animation phase ───────────────────────────────────────────────────────
    while time.ticks_diff(time.ticks_ms(), start) < _ANIM_MS:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            if _sound_ok:
                sound.stop(su)
            return interrupted_by

        elapsed = time.ticks_diff(time.ticks_ms(), start)
        by = _bee_y(elapsed / _ANIM_MS, amp)
        _draw_bee(graphics, _BX, by, wing_shift)
        su.update(graphics)

        wing_shift = 1 - wing_shift
        time.sleep_ms(33)

    # ── hold phase ────────────────────────────────────────────────────────────
    hold_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), hold_start) < _HOLD_MS:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by

        _draw_bee(graphics, _BX, _BY_CENTRE, wing_shift)
        su.update(graphics)
        wing_shift = 1 - wing_shift
        time.sleep_ms(50)

    return None
