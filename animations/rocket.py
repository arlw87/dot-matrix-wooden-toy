"""
Rocket animation — green-body rocket launches from bottom to top.
Wired to GPB0 (green button).  Replaces fish.

Coordinate convention (display.pixel):
  x = 0 is the bottom row of the physical display, x = 15 is the top row.
  y = 0 is the left column,  y = 15 is the right column.
The rocket rises, so rx (nose x) increases over time.

Rocket layout relative to nose position rx (centred at y = 7–8):
  Nose cone  — 3 rows, tapering 2 → 4 → 6 wide       (red)
  Body       — 4 rows, 6 wide  (y = 5–10)             (green)
  Window     — 2 × 2 in centre of body                (magnolia)
  Fins row 1 — (rx-7): y=3,4 + y=5–10 + y=11,12      (red + green + red, 10 wide)
  Fins row 2 — (rx-8): y=2,3,4 + y=5–10 + y=11,12,13 (red + green + red, 12 wide)
  Flame      — 1–3 rows below fins                    (orange → yellow)
"""

import time
from lib import display, sound

SOUND_FILE = "sounds/rocket.wav"

# ── colours ───────────────────────────────────────────────────────────────────
_BODY = (30,  155,  50)    # green body
_NOSE = (210,  30,  20)    # red nose cone + fins
_WIN  = (240, 240, 215)    # magnolia window
_FL_O = (220,  85,  10)    # deep orange (closest to nozzle)
_FL_M = (255, 145,  20)    # orange mid
_FL_H = (255, 210,  40)    # yellow hot tip

# ── travel range ──────────────────────────────────────────────────────────────
_START_RX = 7    # nose x at launch — body enters from bottom edge
_END_RX   = 23   # nose x when fully off the top of the display


def _px(graphics, x, y, r, g, b):
    """Draw one pixel, clipping anything outside the 16×16 grid."""
    if 0 <= x < 16 and 0 <= y < 16:
        graphics.set_pen(graphics.create_pen(r, g, b))
        display.pixel(graphics, x, y)


def _draw_rocket(graphics, rx, flame_len, flame_seed):
    """Draw the rocket with its nose tip at logical x = rx."""

    # Nose cone (3 rows, tapering)
    _px(graphics, rx,     7, *_NOSE)
    _px(graphics, rx,     8, *_NOSE)
    for y in range(6, 10):
        _px(graphics, rx - 1, y, *_NOSE)
    for y in range(5, 11):
        _px(graphics, rx - 2, y, *_NOSE)

    # Body (4 rows, 6 wide)
    for dx in range(3, 7):
        for y in range(5, 11):
            _px(graphics, rx - dx, y, *_BODY)

    # Window — 2×2 magnolia centred in body (overwrites body at rx-4, rx-5)
    for dx in (4, 5):
        for y in (7, 8):
            _px(graphics, rx - dx, y, *_WIN)

    # Fins row 1 (rx-7): outer cols red, centre green
    for y in (3, 4):
        _px(graphics, rx - 7, y, *_NOSE)
    for y in range(5, 11):
        _px(graphics, rx - 7, y, *_BODY)
    for y in (11, 12):
        _px(graphics, rx - 7, y, *_NOSE)

    # Fins row 2 (rx-8): wider outer cols red, centre green
    for y in (2, 3, 4):
        _px(graphics, rx - 8, y, *_NOSE)
    for y in range(5, 11):
        _px(graphics, rx - 8, y, *_BODY)
    for y in (11, 12, 13):
        _px(graphics, rx - 8, y, *_NOSE)

    # Flame outer row (4 wide, always present when rx-9 is in frame)
    for y in range(6, 10):
        _px(graphics, rx - 9, y, *_FL_O)

    # Flame mid row — wide or narrow based on flicker seed
    if flame_len >= 2:
        fy = range(5, 11) if flame_seed % 2 == 0 else range(6, 10)
        for y in fy:
            _px(graphics, rx - 10, y, *_FL_M)

    # Flame hot tip
    if flame_len >= 3:
        for y in (7, 8):
            _px(graphics, rx - 11, y, *_FL_H)


def play(su, graphics, check_interrupt=None):
    """
    Play the rocket animation.
    Returns None on completion, or a button name (str) if interrupted.
    """
    _sound_started = False
    try:
        sound.play(su, SOUND_FILE)
        _sound_started = True
    except OSError:
        pass

    start_time = time.ticks_ms()
    animation_duration_ms = 5000
    frame = 0

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            if _sound_started:
                sound.stop(su)
            return interrupted_by

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        progress = (t / 5.0) ** 1.5   # ease-in: accelerates upward
        rx = int(_START_RX + (_END_RX - _START_RX) * progress)

        frame += 1
        flame_len = 3 if frame % 3 == 0 else 2
        flame_seed = frame % 2

        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        _draw_rocket(graphics, rx, flame_len, flame_seed)
        su.update(graphics)
        time.sleep_ms(33)

    # Hold phase — rocket off screen, blank display
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
