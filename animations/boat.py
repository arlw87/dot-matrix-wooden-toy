"""
Boat animation — front-wheelhouse trawler drifts left→right on animated water.
Wired to GPB1 (blue button).

Display coordinate convention (matches rocket.py):
  x = 0  bottom row,  x = 15  top row
  y = 0  left column, y = 15  right column

Boat layout at base position (drift=0, bob=0):
  Water surface  x=1, y=0-15  (animated shimmer)
  Water mid      x=2, y=0-15  (shimmers between surface and depth colours)
  Water depth    x=0, y=0-15
  Keel           x=2, y=3-12  (overdraws water mid)
  Hull           x=3, y=2-13
  Hull           x=4, y=1-14
  Deck           x=5, y=2-13
  Wheelhouse     x=6-9, y=2-6  (stern — enters screen last)
  Windows        x=7-8, y=3-4
  Antenna        x=10-12, y=4

drift: y-offset for horizontal position.
  Starts at -13 (open bow just entering from left), ends at +1 (hold position).
bob: x-offset for vertical bob.
  +1 = up (cresting wave), -1 = down (keel dips into water surface), 0 = rest.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/boat.wav"

_HULL_A = (190,  55,  15)   # orange hull
_HULL_B = (140,  35,   8)   # dark orange lower hull / keel
_CABIN  = (245, 245, 245)   # white wheelhouse
_WINDOW = ( 30,  50,  90)   # dark blue windows
_DETAIL = (220, 180,  90)   # gold antenna
_W_SURF = (  0, 255, 200)   # near-cyan water surface (x=1)
_W_DEEP = (  0, 200, 255)   # aqua water depth        (x=0)


def _px(graphics, x, y, colour):
    if 0 <= x < 16 and 0 <= y < 16:
        graphics.set_pen(graphics.create_pen(*colour))
        display.pixel(graphics, x, y)


def _draw_water(graphics, phase):
    """Three rows of water with a travelling sine-wave shimmer."""
    for y in range(16):
        wave = 0.5 + 0.5 * math.sin(y * 1.2 + phase)
        # surface (x=1): near-cyan, shimmer on blue channel
        b_surf = int(_W_SURF[2] + wave * 30)  # 200–230
        _px(graphics, 1, y, (_W_SURF[0], _W_SURF[1], b_surf))
        # mid (x=2): shimmers between _W_DEEP and _W_SURF by blending g and b
        g_mid = int(_W_DEEP[1] + wave * (_W_SURF[1] - _W_DEEP[1]))  # 200–255
        b_mid = int(_W_DEEP[2] + wave * (_W_SURF[2] - _W_DEEP[2]))  # 255–200
        _px(graphics, 2, y, (0, g_mid, b_mid))
        _px(graphics, 0, y, _W_DEEP)


def _draw_boat(graphics, drift, bob):
    """Draw the boat at the given horizontal drift and vertical bob offsets."""
    # Hull (bottom to top)
    for y in range(3 + drift, 13 + drift): _px(graphics, 2 + bob, y, _HULL_B)  # keel
    for y in range(2 + drift, 14 + drift): _px(graphics, 3 + bob, y, _HULL_B)  # lower hull
    for y in range(1 + drift, 15 + drift): _px(graphics, 4 + bob, y, _HULL_A)  # upper hull
    for y in range(2 + drift, 14 + drift): _px(graphics, 5 + bob, y, _HULL_A)  # deck

    # Wheelhouse (stern, low-y side of boat — enters screen last)
    for x in range(6 + bob, 10 + bob):
        for y in range(2 + drift, 7 + drift):
            _px(graphics, x, y, _CABIN)

    # Windows
    for x in (7 + bob, 8 + bob):
        for y in (3 + drift, 4 + drift):
            _px(graphics, x, y, _WINDOW)

    # Antenna
    for x in range(10 + bob, 13 + bob):
        _px(graphics, x, 4 + drift, _DETAIL)


def play(su, graphics, check_interrupt=None):
    """
    Play the boat animation.
    Returns None on completion, or the button name if interrupted.
    """
    _sound_started = False
    try:
        sound.play(su, SOUND_FILE)
        _sound_started = True
    except OSError:
        pass

    bob_period = 1.8 + random.uniform(-0.3, 0.3)    # bob cycle in seconds
    wave_speed = 0.15 + random.uniform(-0.03, 0.03)  # wave phase step per frame

    drift_start = -13
    drift_end   = 1
    anim_ms     = 5000
    hold_ms     = 5000

    start      = time.ticks_ms()
    wave_phase = 0.0

    # ── animation phase ───────────────────────────────────────────────────────
    while True:
        interrupted = check_interrupt() if check_interrupt else None
        if interrupted:
            if _sound_started:
                sound.stop(su)
            return interrupted

        elapsed = time.ticks_diff(time.ticks_ms(), start)
        if elapsed >= anim_ms:
            break

        t = elapsed / 1000.0
        drift = int(drift_start + (drift_end - drift_start) * t / (anim_ms / 1000.0))
        bob_raw = math.sin(t * 2 * math.pi / bob_period)
        bob = 1 if bob_raw > 0.35 else (-1 if bob_raw < -0.35 else 0)
        wave_phase += wave_speed

        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        _draw_water(graphics, wave_phase)
        _draw_boat(graphics, drift, bob)
        su.update(graphics)
        time.sleep_ms(33)

    # ── hold phase ────────────────────────────────────────────────────────────
    hold_start = time.ticks_ms()
    while True:
        interrupted = check_interrupt() if check_interrupt else None
        if interrupted:
            if _sound_started:
                sound.stop(su)
            return interrupted

        elapsed = time.ticks_diff(time.ticks_ms(), hold_start)
        if elapsed >= hold_ms:
            break

        t_hold = elapsed / 1000.0
        bob_raw = math.sin(t_hold * 2 * math.pi / bob_period)
        bob = 1 if bob_raw > 0.35 else (-1 if bob_raw < -0.35 else 0)
        wave_phase += wave_speed

        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        _draw_water(graphics, wave_phase)
        _draw_boat(graphics, drift_end, bob)
        su.update(graphics)
        time.sleep_ms(33)

    if _sound_started:
        sound.stop(su)
    return None
