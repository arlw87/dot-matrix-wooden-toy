"""
Tilt Game — a ball rolls around the 16x16 display driven by KX134 tilt.

The ball accelerates with gravity (accelerometer X/Y), bounces elastically off
the four edges (losing a little energy each time), changes colour by direction
of travel, and leaves a fading trail. Light friction lets it settle when the
toy is held level. Entered/exited from main.py by holding yellow+red for 5s.

Physics (TiltBall) is pure and hardware-free so it can be unit-tested; run()
wires it to the KX134, display and sound.
"""

import time

from lib import display, sound

BOUNCE_SOUND = "sounds/bounce.wav"   # plays on each wall hit if present (issue #10)
FRAME_MS = 33            # ~30 fps
STILL_SLEEP_MS = 2 * 60 * 1000   # held still this long → return SLEEP
TRAIL_LEN = 8            # number of past positions kept in the fading trail
TRAIL_MAX_BRIGHT = 0.6   # brightest a trail pixel gets (ball itself is full)

# run() return values
EXIT = "exit"    # player exited via the yellow+red toggle
SLEEP = "sleep"  # ball sat still long enough to auto-sleep

# A 1px white frame runs around the edge of the display; the ball bounces off
# the inside of it and never overlaps it.
BORDER = 1
WHITE = (255, 255, 255)

# Ball geometry — a 2x2 block. (x, y) is the top-left continuous position.
BALL_SIZE = 2
MIN_POS = float(BORDER)                    # 1.0 — just inside the frame
MAX_POS = 16.0 - BORDER - BALL_SIZE        # 13.0 — 2x2 block stays off the frame
CENTRE = (MIN_POS + MAX_POS) / 2.0         # 7.0

# Physics tuning (pixels/frame; adjust on real hardware)
ACCEL_SCALE = 0.15   # G-force → velocity delta per frame (lower = less sensitive)
DEADZONE = 0.04      # ignore tilts below this many g (sensor noise / not-quite-level)
BOUNCE_DAMP = 0.6    # fraction of speed kept after a wall bounce (energy loss)
BOUNCE_MIN_SPEED = 0.4  # min impact speed that counts as a bounce (plays sound)
FRICTION = 0.92      # fraction of velocity kept each frame (lets it settle)
ACTIVITY_SPEED = 0.15  # min speed (px/frame) counted as Tilt Activity

# Direction → colour (veneer-safe palette; see display-color-visibility memory).
# Mapping of axis sign to physical direction may need flipping on hardware.
RED    = (255, 0, 0)      # moving +x ("right")
AQUA   = (0, 200, 255)    # moving -x ("left") — Aqua, never plain blue
YELLOW = (255, 255, 0)    # moving +y ("up")
GREEN  = (0, 255, 0)      # moving -y ("down")


def _direction_colour(vx, vy):
    """Veneer-safe colour for a velocity's dominant axis (up/down/left/right)."""
    if abs(vx) >= abs(vy):
        return RED if vx >= 0 else AQUA
    return YELLOW if vy >= 0 else GREEN


def sensor_to_tilt(raw_x, raw_y):
    """
    Map raw KX134 X/Y G-force to display tilt (ax = vertical, ay = horizontal).

    The KX134 breakout is mounted rotated 90° relative to the display, so the
    sensor's X axis is the screen's horizontal and its Y axis is the screen's
    vertical. This 90° rotation makes the ball roll toward the lowered edge:
      raw right-edge-down (raw_x < 0) → ay > 0 → ball rolls right
      raw top-edge-down   (raw_y > 0) → ax > 0 → ball rolls up
    If the ball still moves wrong on hardware, adjust this one function.

    A per-axis deadzone first discards tiny readings (sensor noise and the toy
    never being perfectly level), so a still, level toy leaves the ball at rest.
    """
    raw_x = 0.0 if abs(raw_x) < DEADZONE else raw_x
    raw_y = 0.0 if abs(raw_y) < DEADZONE else raw_y
    return raw_y, -raw_x


class TiltBall:
    """Continuous ball position/velocity in display pixel space."""

    def __init__(self, x=CENTRE, y=CENTRE):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self._colour = RED         # follows the tilt direction; held when level

    def step(self, ax, ay):
        """
        Advance one frame given accelerometer X/Y G-force.

        Gravity accelerates the ball, velocity moves it. Returns True if the
        ball bounced off a wall this frame.
        """
        # Colour follows the tilt (roll) direction and holds when the toy is
        # level. Using the tilt input — not velocity — means wall rebounds,
        # which reverse velocity but not the tilt, never recolour the ball.
        if ax != 0.0 or ay != 0.0:
            self._colour = _direction_colour(ax, ay)

        self.vx = (self.vx + ax * ACCEL_SCALE) * FRICTION
        self.vy = (self.vy + ay * ACCEL_SCALE) * FRICTION
        self.x += self.vx
        self.y += self.vy

        # Clamp to the walls and reverse (with energy loss). A collision only
        # counts as a bounce — and plays a sound — if the impact was fast
        # enough; a ball merely resting against a wall does not re-trigger.
        bounced = False
        if self.x < MIN_POS or self.x > MAX_POS:
            self.x = MIN_POS if self.x < MIN_POS else MAX_POS
            if abs(self.vx) >= BOUNCE_MIN_SPEED:
                bounced = True
            self.vx = -self.vx * BOUNCE_DAMP
        if self.y < MIN_POS or self.y > MAX_POS:
            self.y = MIN_POS if self.y < MIN_POS else MAX_POS
            if abs(self.vy) >= BOUNCE_MIN_SPEED:
                bounced = True
            self.vy = -self.vy * BOUNCE_DAMP

        return bounced

    def colour(self):
        """
        Return the ball's colour: the direction the toy is being tilted.

        Set from the tilt input in step() and held steady when the toy is level,
        so wall rebounds (which reverse velocity, not tilt) never recolour it.
        """
        return self._colour

    def is_moving(self):
        """True while the ball is travelling fast enough to count as Tilt Activity."""
        return (self.vx * self.vx + self.vy * self.vy) >= ACTIVITY_SPEED ** 2


def _draw_block(graphics, x, y, colour):
    """Draw a BALL_SIZE x BALL_SIZE block with its top-left at (x, y)."""
    r, g, b = colour
    graphics.set_pen(graphics.create_pen(r, g, b))
    for dx in range(BALL_SIZE):
        for dy in range(BALL_SIZE):
            display.pixel(graphics, x + dx, y + dy)


def _draw_border(graphics):
    """Draw the 1px white frame around the edge of the display."""
    graphics.set_pen(graphics.create_pen(*WHITE))
    last = 15
    for i in range(16):
        display.pixel(graphics, i, 0)
        display.pixel(graphics, i, last)
        display.pixel(graphics, 0, i)
        display.pixel(graphics, last, i)


def _render(graphics, su, ball, trail):
    """Clear the buffer, draw the frame, the fading trail, then the ball.

    Clears the off-screen buffer directly (not display.clear, which would push
    an extra black frame each loop and cause visible flicker).
    """
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    _draw_border(graphics)

    # Trail: oldest (front of list) is dimmest, newest is brightest.
    n = len(trail)
    for i, (tx, ty, colour) in enumerate(trail):
        factor = TRAIL_MAX_BRIGHT * (i + 1) / (n + 1)
        r, g, b = colour
        _draw_block(graphics, tx, ty, (int(r * factor), int(g * factor), int(b * factor)))

    ix = int(round(ball.x))
    iy = int(round(ball.y))
    _draw_block(graphics, ix, iy, ball.colour())
    su.update(graphics)


def run(su, graphics, kx, should_exit=None):
    """
    Run the Tilt Game until the player exits or the ball settles.

    should_exit() is polled each frame (the yellow+red hold from main.py).
    Returns EXIT if the player toggled out, or SLEEP if the ball has been
    still for STILL_SLEEP_MS.
    """
    ball = TiltBall()
    trail = []
    last_active = time.ticks_ms()

    while True:
        if should_exit and should_exit():
            return EXIT

        ax, ay = sensor_to_tilt(*kx.read_xy())
        if ball.step(ax, ay):
            try:
                sound.play(su, BOUNCE_SOUND)
            except OSError:
                pass   # bounce.wav not present yet (issue #10) — stay silent

        # Record this position for the fading trail (keep the last TRAIL_LEN).
        trail.append((int(round(ball.x)), int(round(ball.y)), ball.colour()))
        if len(trail) > TRAIL_LEN:
            trail.pop(0)

        now = time.ticks_ms()
        if ball.is_moving():
            last_active = now
        elif time.ticks_diff(now, last_active) >= STILL_SLEEP_MS:
            return SLEEP

        _render(graphics, su, ball, trail)
        time.sleep_ms(FRAME_MS)
