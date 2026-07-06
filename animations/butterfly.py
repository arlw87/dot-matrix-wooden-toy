"""
Butterfly animation - colourful butterfly with flapping wings.
Plays for ~5 seconds then holds the final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/butterfly.wav"

# Body and antennae — pink so they stand out
_BODY     = (255,  80, 160)
_ANTENNA  = (255,  80, 160)
_SPOT     = (255, 255, 255)

# Wing colours, warm→cool from body outward
_WING = [
    (255,  50, 150),  # pink  (nearest to body)
    (255, 100,  50),  # orange
    (255, 255,   0),  # yellow
    (100, 200, 255),  # light blue
    (200, 100, 255),  # purple
]


def _draw(pixels, x, y, colour):
    """Append a pixel only if it's within the 16×16 grid."""
    if 0 <= x < 16 and 0 <= y < 16:
        pixels.append((x, y, colour[0], colour[1], colour[2]))


def get_butterfly_pixels(cx, cy, wing_angle, spread=None):
    """
    Return a list of (x, y, r, g, b) tuples for the butterfly.
    cx/cy are the body centre (float-safe); wing_angle drives the flap.
    spread (0.0–1.0) overrides the angle-derived spread when provided.
    In butterfly coords: x = column (left=0), y = row (top=0 after display mapping).
    """
    pixels = []
    if spread is None:
        spread = 0.5 + 0.5 * math.sin(wing_angle)

    # ── Body (8 pixels tall, centred at cy) ──────────────────────────────────
    for dy in range(-4, 4):
        _draw(pixels, int(cx), int(cy + dy), _BODY)

    # ── Upper wings — wider than before to fill the screen width ─────────────
    upper_width  = min(7, int(6 * spread) + 2)   # 2–7 columns from body at spread 0→1
    upper_height = 5

    for side in (-1, 1):
        for wy in range(upper_height):
            row_w = max(1, upper_width - wy // 2)
            for wx in range(1, row_w + 1):
                x = int(cx + side * wx)
                y = int(cy - 3 + wy)
                _draw(pixels, x, y, _WING[min(wx - 1, len(_WING) - 1)])

    # ── Lower wings ───────────────────────────────────────────────────────────
    lower_width  = int(4 * spread) + 1   # 1–5 columns from body
    lower_height = 4

    for side in (-1, 1):
        for wy in range(lower_height):
            row_w = max(1, lower_width - abs(wy - 1))
            for wx in range(1, row_w + 1):
                x = int(cx + side * wx)
                y = int(cy + 1 + wy)
                _draw(pixels, x, y, _WING[(min(wx - 1, len(_WING) - 1) + 2) % len(_WING)])

    # ── White wing spots ──────────────────────────────────────────────────────
    for side in (-1, 1):
        _draw(pixels, int(cx + side * max(1, int(3 * spread + 1))),
              int(cy - 1), _SPOT)
        _draw(pixels, int(cx + side * max(1, int(2 * spread + 1))),
              int(cy + 2), _SPOT)

    # ── Antennae — pink, 3 pixels each, diagonal outward from head ────────────
    for side in (-1, 1):
        for step in range(3):
            _draw(pixels, int(cx + side * (step + 1)), int(cy - 4 - step), _ANTENNA)

    return pixels


def _render(graphics, su, cx, cy, wing_angle, spread=None):
    """Clear display and draw the butterfly at the given state."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    for x, y, r, g, b in get_butterfly_pixels(cx, cy, wing_angle, spread):
        graphics.set_pen(graphics.create_pen(r, g, b))
        display.pixel(graphics, 15 - y, x)
    su.update(graphics)


def play(su, graphics, check_interrupt=None):
    """
    Play the butterfly flapping animation.
    Returns None if completed normally, or the button name (str) if interrupted.
    """
    flap_speed = 4.0 + random.uniform(-0.5, 0.5)

    sound.play(su, SOUND_FILE)

    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    cx, cy = 8, 8

    _SETTLE_START = 4.5   # seconds into animation when wings begin settling
    _FULL_SPREAD  = 1.0   # target spread for hold frame

    # ── Animation phase ───────────────────────────────────────────────────────
    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            sound.stop(su)
            return interrupted_by

        t          = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        wing_angle = t * flap_speed * math.pi
        bob        = math.sin(t * 2) * 0.5

        # In the last 0.5 s ease spread → 1.0 and bob → 0 so the final
        # animation frame is identical to the hold frame.
        if t >= _SETTLE_START:
            ease       = min(1.0, (t - _SETTLE_START) / 0.5)
            spread     = (0.5 + 0.5 * math.sin(wing_angle)) * (1.0 - ease) + _FULL_SPREAD * ease
            settled_cy = (cy + bob) * (1.0 - ease) + float(cy) * ease
        else:
            spread     = None
            settled_cy = cy + bob

        _render(graphics, su, cx, settled_cy, wing_angle, spread)
        time.sleep_ms(33)

    # ── Hold phase — wings fully spread (matches final animation frame) ───────
    sound.stop(su)
    _render(graphics, su, cx, float(cy), 0.0, _FULL_SPREAD)

    hold_start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), hold_start) < 5000:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
