"""
Flower animation - a gold centre circle appears, then warm-pink petals
grow outward from its edge. Same every play, no variation.
"""

import time
import math
from lib import display, sound

SOUND_FILE = "sounds/flower.wav"

_CX, _CY       = 7.5, 7.5
_CIRCLE_R      = 2.0   # radius of centre circle
_PETAL_A_MAX   = 2.5   # petal semi-major axis (length from ellipse centre to tip)
_PETAL_B_MAX   = 1.5   # petal semi-minor axis (half-width at full size)
_NUM_PETALS    = 8

_CENTER_COLOR  = (255, 210, 50)   # warm gold
_PETAL_COLOR   = (255, 80, 130)   # warm pink


def _draw_filled_circle(graphics, cx, cy, radius):
    """Draw a filled circle using the current pen."""
    r2 = radius * radius
    for y in range(int(cy - radius) - 1, int(cy + radius) + 2):
        for x in range(int(cx - radius) - 1, int(cx + radius) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                if 0 <= x < 16 and 0 <= y < 16:
                    display.pixel(graphics, x, y)


def _draw_petal(graphics, angle, semi_major):
    """Draw one elliptical petal anchored at the centre circle edge."""
    dx_u =  math.cos(angle)
    dy_u =  math.sin(angle)
    px_u = -dy_u              # perpendicular unit vector
    py_u =  dx_u

    # Ellipse centre sits so the near end always touches the circle edge
    pcx = _CX + (_CIRCLE_R + semi_major) * dx_u
    pcy = _CY + (_CIRCLE_R + semi_major) * dy_u

    a = semi_major
    b = min(_PETAL_B_MAX, semi_major * 0.7)  # width grows with length

    search = a + 1
    y0, y1 = int(pcy - search) - 1, int(pcy + search) + 2
    x0, x1 = int(pcx - search) - 1, int(pcx + search) + 2
    for y in range(y0, y1):
        for x in range(x0, x1):
            along = (x - pcx) * dx_u + (y - pcy) * dy_u
            perp  = (x - pcx) * px_u + (y - pcy) * py_u
            if (along / a) ** 2 + (perp / b) ** 2 <= 1.0:
                if 0 <= x < 16 and 0 <= y < 16:
                    display.pixel(graphics, x, y)


def _draw_flower(graphics, circle_r, petal_a):
    """Render the complete flower at the given growth state."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    # Petals first (drawn behind centre)
    if petal_a > 0:
        graphics.set_pen(graphics.create_pen(*_PETAL_COLOR))
        for i in range(_NUM_PETALS):
            angle = (i / _NUM_PETALS) * 2 * math.pi
            _draw_petal(graphics, angle, petal_a)

    # Centre circle on top
    if circle_r > 0:
        graphics.set_pen(graphics.create_pen(*_CENTER_COLOR))
        _draw_filled_circle(graphics, _CX, _CY, circle_r)


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

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        progress = t / 5.0  # 0.0 → 1.0 over 5 seconds

        # Phase 1 (first 25%): centre circle grows in
        circle_r = _CIRCLE_R * min(1.0, progress / 0.25)

        # Phase 2 (remaining 75%): petals grow outward from circle edge
        petal_a = _PETAL_A_MAX * max(0.0, (progress - 0.25) / 0.75)

        _draw_flower(graphics, circle_r, petal_a)
        su.update(graphics)
        time.sleep_ms(33)

    # Hold phase — full bloom for 5 seconds
    _draw_flower(graphics, _CIRCLE_R, _PETAL_A_MAX)
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
