"""
Fish animation - a large purple fish swims in from the right and stops
just past the centre of the display, then holds for 5 seconds.
sounds/fish.wav plays if present; runs silently if the file is absent.

Coordinate note: display.pixel(x, y) applies 90° rotation internally:
  physical column (left→right) = logical y
  physical row    (top→bottom) = 15 − logical x
So to swim horizontally the fish must vary CY, not CX.
"""

import time
import math
from lib import display, sound

SOUND_FILE = "sounds/fish.wav"

_BR, _BG, _BB = 170, 30, 230   # vivid purple body
_FR, _FG, _FB = 110, 15, 170   # deeper purple tail

_CX       =  8.0   # fixed vertical centre (physical row = 15-8 = 7)
_START_CY = 22.0   # fish centre starts off-screen right (physical col > 15)
_STOP_CY  =  7.0   # fish centre rests just left of display centre (col=7)

# Body pixels — filled ellipse: semi-major 5 in DY (horizontal), semi-minor 2.5 in DX (vertical)
_BODY = []
for _dx in range(-3, 4):
    for _dy in range(-5, 6):
        if (_dx * _dx) / 6.25 + (_dy * _dy) / 25.0 <= 1.0:
            _BODY.append((_dx, _dy))

# Tail offsets — positive DY = right side of screen (behind a left-swimming fish)
_TAIL = [
    (-1, 5), (1, 5),
    (-1, 6), (0, 6), (1, 6),
    (-2, 7), (-1, 7), (1, 7), (2, 7),
    (-2, 8), (2, 8),
]


def _draw_fish(graphics, cx, cy):
    for dx, dy in _BODY:
        x = int(round(cx + dx))
        y = int(round(cy + dy))
        if 0 <= x < 16 and 0 <= y < 16:
            graphics.set_pen(graphics.create_pen(_BR, _BG, _BB))
            display.pixel(graphics, x, y)

    for dx, dy in _TAIL:
        x = int(round(cx + dx))
        y = int(round(cy + dy))
        if 0 <= x < 16 and 0 <= y < 16:
            graphics.set_pen(graphics.create_pen(_FR, _FG, _FB))
            display.pixel(graphics, x, y)


def play(su, graphics, check_interrupt=None):
    """
    Play the fish animation.

    Returns None if completed normally, button name (str) if interrupted.
    """
    _sound_started = False
    try:
        sound.play(su, SOUND_FILE)
        _sound_started = True
    except OSError:
        pass

    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            if _sound_started:
                sound.stop(su)
            return interrupted_by

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        # Ease-out: decelerates as fish reaches stop position
        ease = 1.0 - (1.0 - t / 5.0) * (1.0 - t / 5.0)
        cy = _START_CY + (_STOP_CY - _START_CY) * ease

        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        _draw_fish(graphics, _CX, cy)
        su.update(graphics)
        time.sleep_ms(33)

    # Hold phase — fish at rest position
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    _draw_fish(graphics, _CX, _STOP_CY)
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
