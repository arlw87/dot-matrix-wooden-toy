"""
Tilt Ball — roll a glowing ball around the 16×16 matrix by tilting the toy.
The ball leaves a colour-shifting trail and bounces off the walls.

Exit: double-tap the toy surface, or press any button.
"""

import time
import math
from lib import display

# ── Physics constants ─────────────────────────────────────────────────────────
_GRAVITY   = 0.35   # how strongly tilt accelerates the ball
_FRICTION  = 0.87   # velocity multiplier per frame (damping)
_BOUNCE    = 0.45   # fraction of speed kept on wall collision
_TRAIL_LEN = 7      # number of ghost pixels behind the ball
_FRAME_MS  = 33     # ~30 fps


def _hsv(h, s, v):
    """Convert HSV (h=0-360, s/v=0-1) → (r, g, b) 0-255."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def _entry_flash(su, graphics):
    """Brief blue ripple to signal entering ball mode."""
    cx, cy = 7.5, 7.5
    for radius in range(1, 13):
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        for y in range(16):
            for x in range(16):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if abs(dist - radius) < 1.5:
                    brightness = int(200 * (1 - abs(dist - radius) / 1.5))
                    graphics.set_pen(graphics.create_pen(0, brightness // 3, brightness))
                    display.pixel(graphics, x, y)
        su.update(graphics)
        time.sleep_ms(40)
    display.clear(graphics, su)
    time.sleep_ms(80)


def run(su, graphics, check_exit):
    """
    Run the tilt ball game.

    Args:
        su:         StellarUnicorn instance
        graphics:   PicoGraphics instance
        check_exit: callable → True to stop, False to continue

    If the accelerometer axes feel inverted, flip the sign of ax or ay
    in the velocity update below to match your board mounting.
    """
    from lib import bma400

    _entry_flash(su, graphics)

    # Small debounce delay so the entry double-tap doesn't immediately exit
    time.sleep_ms(600)

    # Ball state
    bx, by = 7.5, 7.5  # position in [0, 15]
    vx, vy = 0.0, 0.0
    trail  = []         # list of (x, y) historical positions
    hue    = 0.0        # rolling hue for colour shift

    while not check_exit():
        ax, ay, _ = bma400.read_xyz()

        # Tilt → velocity  (flip ax/ay signs here if ball rolls the wrong way)
        vx +=  ax * _GRAVITY
        vy +=  ay * _GRAVITY

        # Dampen
        vx *= _FRICTION
        vy *= _FRICTION

        # Move
        bx += vx
        by += vy

        # Bounce off walls
        if bx < 0.0:
            bx = 0.0
            vx = abs(vx) * _BOUNCE
        elif bx > 15.0:
            bx = 15.0
            vx = -abs(vx) * _BOUNCE

        if by < 0.0:
            by = 0.0
            vy = abs(vy) * _BOUNCE
        elif by > 15.0:
            by = 15.0
            vy = -abs(vy) * _BOUNCE

        # Hue shifts faster when moving quickly
        speed = math.sqrt(vx * vx + vy * vy)
        hue = (hue + 1.2 + speed * 5) % 360

        # Record trail
        trail.append((bx, by))
        if len(trail) > _TRAIL_LEN:
            trail.pop(0)

        # ── Draw frame ────────────────────────────────────────────────────────
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        # Trail: older positions are dimmer
        n = len(trail) - 1  # exclude the current position (drawn as the ball)
        for i, (tx, ty) in enumerate(trail[:-1]):
            fade = (i + 1) / _TRAIL_LEN * 0.45
            r, g, b = _hsv(hue - (n - i) * 8, 0.9, fade)
            graphics.set_pen(graphics.create_pen(r, g, b))
            display.pixel(graphics, int(tx), int(ty))

        # Soft glow ring around ball
        gr, gg, gb = _hsv(hue, 0.5, 0.25)
        graphics.set_pen(graphics.create_pen(gr, gg, gb))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = int(bx) + dx, int(by) + dy
            if 0 <= nx <= 15 and 0 <= ny <= 15:
                display.pixel(graphics, nx, ny)

        # Ball centre (full brightness)
        r, g, b = _hsv(hue, 1.0, 1.0)
        graphics.set_pen(graphics.create_pen(r, g, b))
        display.pixel(graphics, int(bx), int(by))

        su.update(graphics)
        time.sleep_ms(_FRAME_MS)

    display.clear(graphics, su)
