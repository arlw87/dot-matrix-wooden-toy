"""
Rocket Blast-off — shake the toy to fly a rocket up and launch it into space.

Aimed at a 2-year-old: pure cause-and-effect with a big, reliable gesture.
The rocket sits on the ground. Shaking the toy thrusts it upward (a whoosh plays
once as each flight begins) and grows its flame; stop shaking and gravity gently
lowers it back down. Keep shaking and it climbs off the top of the display —
BLAST OFF — into a shower of twinkling stars with a shimmer sound, before a fresh
rocket drops back to the ground. If it lands first, the next shake starts a new
whoosh. There is no win/lose: shaking is the whole game.
Entered/exited from main.py by holding blue (boat) + pink (butterfly) for 5s.

The game rocket is deliberately its own design — narrower, shorter, and aqua
rather than the green-bodied rocket Animation — so a child (and adult) can tell
the shake game apart from the button animation at a glance.

Physics (Rocket) is pure and hardware-free so it can be unit-tested; run() wires
it to the KX134, display and sound.
"""

import time

from lib import display, sound

LAUNCH_SOUND = "sounds/rocket.wav"    # whoosh played once when a flight's shaking starts, if present
STAR_SOUND   = "sounds/shimmer.wav"   # ~5 s shimmer played over the star shower, if present
FRAME_MS = 33                        # ~30 fps
STILL_SLEEP_MS = 2 * 60 * 1000       # grounded + unshaken this long → SLEEP

# run() return values (mirrors tilt.py)
EXIT = "exit"    # player exited via the boat+butterfly toggle
SLEEP = "sleep"  # left still long enough to auto-sleep

# ── Geometry ──────────────────────────────────────────────────────────────────
# rx is the rocket's nose position in display rows (x = 0 bottom, 15 top). On the
# ground only the top of the rocket peeks up from the bottom edge; at LAUNCH_RX
# the rocket has climbed off the top of the display.
GROUND_RX = 7.0
LAUNCH_RX = 22.0

# ── Physics tuning (per-frame; adjust on real hardware) ───────────────────────
# A 2-year-old's shake reads as a spike in accelerometer magnitude. Shaking adds
# upward velocity (THRUST_SCALE); gravity always pulls back; drag keeps it from
# running away so it settles when the shaking stops. Tuned to launch on moderate
# shaking — between a very-easy and a stiff feel.
SHAKE_DEADZONE = 0.28   # g away from 1 g before it counts as a shake (noise floor)
THRUST_SCALE   = 0.30   # shake amount → upward velocity delta per frame
MAX_SHAKE      = 2.0    # shake is capped here — shaking harder adds no more thrust
GRAVITY        = 0.22   # downward pull per frame
DRAG           = 0.87   # fraction of velocity kept each frame (settles the rocket)
ACTIVE_SPEED   = 0.05   # |vy| above this counts as airborne activity (resets sleep)

# Set True to print shake/height telemetry ~2x/second while the game runs, to
# help tune SHAKE_DEADZONE/THRUST_SCALE/GRAVITY/DRAG on real hardware. Turn off
# once the physics feels right — the prints are noise in normal play.
DEBUG = True
_DEBUG_INTERVAL_MS = 500

# ── Colours (veneer-safe; see display-color-visibility memory) ────────────────
_BODY = (0, 200, 255)     # aqua body — the game rocket's signature colour
_NOSE = (210,  30,  20)   # red nose cone + fins
_WIN  = (240, 240, 215)   # magnolia window
_FL_O = (220,  85,  10)   # deep orange (nearest the nozzle)
_FL_H = (255, 210,  40)   # yellow hot tip
_FL_X = (255, 245, 120)   # pale yellow extreme tip

# ── Star-shower launch flash ──────────────────────────────────────────────────
_STAR_SOFT = (240, 240, 215)   # magnolia
_STAR_HOT  = (255, 210, 40)    # warm yellow
_LAUNCH_FLASH_FRAMES = 160   # star shower lingers ~5.3 s to cover the shimmer sound
_STARS = [
    (2, 3), (4, 12), (6, 6), (9, 1), (11, 9), (13, 4),
    (3, 9), (7, 13), (8, 5), (10, 14), (12, 2), (14, 11),
    (1, 7), (5, 1), (9, 10), (13, 8),
]


def shake_amount(x, y, z):
    """
    How hard the toy is being shaken, from raw KX134 X/Y/Z G-force.

    A still toy reads ~1 g total (gravity). Shaking swings the total magnitude
    away from 1 g, so |magnitude - 1| is a simple, orientation-independent shake
    measure. Readings within SHAKE_DEADZONE are treated as no shake so a resting
    toy leaves the rocket on the ground. Never negative.
    """
    mag = (x * x + y * y + z * z) ** 0.5
    dev = abs(mag - 1.0)
    return dev if dev >= SHAKE_DEADZONE else 0.0


class Rocket:
    """Continuous rocket height/velocity, driven by shake energy."""

    def __init__(self):
        self.rx = GROUND_RX
        self.vy = 0.0
        self.launched = False

    def step(self, shake):
        """
        Advance one frame given a shake amount (>= 0).

        Shaking adds upward velocity; gravity always pulls down; drag damps it.
        The shake is capped at MAX_SHAKE, so shaking harder than that adds no
        extra thrust — the rocket can't climb faster than a MAX_SHAKE shake. The
        rocket rests on the ground and never sinks below it. Returns True on the
        frame the rocket clears the top of the display (launch).
        """
        thrust = min(shake, MAX_SHAKE) * THRUST_SCALE
        self.vy = (self.vy + thrust - GRAVITY) * DRAG
        self.rx += self.vy

        if self.rx <= GROUND_RX:
            self.rx = GROUND_RX
            if self.vy < 0.0:
                self.vy = 0.0

        if self.rx >= LAUNCH_RX:
            self.launched = True
        return self.launched

    def is_active(self, shake):
        """True while being shaken or airborne — used to hold off auto-sleep."""
        return shake > 0.0 or self.rx > GROUND_RX + 0.5 or abs(self.vy) > ACTIVE_SPEED


def _flame_len(shake, vy):
    """Flame length (2–3) grows with how hard the rocket is being driven."""
    drive = shake + max(0.0, vy)
    if drive >= 1.2:
        return 3
    if drive >= 0.5:
        return 2
    return 1


def _px(graphics, x, y, r, g, b):
    """Draw one pixel, clipping anything outside the 16×16 grid."""
    if 0 <= x < 16 and 0 <= y < 16:
        graphics.set_pen(graphics.create_pen(r, g, b))
        display.pixel(graphics, x, y)


def _draw_rocket(graphics, rx, flame_len):
    """
    Draw the game rocket with its nose tip at logical x = rx.

    Distinct from the rocket Animation: a red nose cone over an aqua body 4
    columns wide (two narrower), a slim single-row 2-pixel window, red fins, and
    a slim 2-wide flame. The body fills columns y = 6–9 from just under the cone
    down to the base level with the fins.
    """
    # Nose cone — 2-wide tip, then a 4-wide flare down to body width.
    for y in (7, 8):
        _px(graphics, rx, y, *_NOSE)
    for y in range(6, 10):
        _px(graphics, rx - 1, y, *_NOSE)

    # Body — aqua, 4 wide, from the row under the cone down to the fin base.
    for dx in (2, 3, 4, 5):
        for y in range(6, 10):
            _px(graphics, rx - dx, y, *_BODY)

    # Window — 2 magnolia pixels on a single row (the top body row stays aqua).
    for y in (7, 8):
        _px(graphics, rx - 3, y, *_WIN)

    # Fins — red, sticking out either side at the base (over the aqua body).
    for y in (5, 10):
        _px(graphics, rx - 4, y, *_NOSE)
    for y in (4, 5, 10, 11):
        _px(graphics, rx - 5, y, *_NOSE)

    # Flame — slim, 2 wide, growing downward with flame_len.
    for y in (7, 8):
        _px(graphics, rx - 6, y, *_FL_O)
    if flame_len >= 2:
        for y in (7, 8):
            _px(graphics, rx - 7, y, *_FL_H)
    if flame_len >= 3:
        for y in (7, 8):
            _px(graphics, rx - 8, y, *_FL_X)


def _render(graphics, su, rocketball, shake):
    """Draw the climbing rocket on a black sky (no border — it flies off the top)."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    rx = int(round(rocketball.rx))
    _draw_rocket(graphics, rx, _flame_len(shake, rocketball.vy))
    su.update(graphics)


def _try_play(su, filename):
    """Play a sound, staying silent if the file isn't present."""
    try:
        sound.play(su, filename)
    except OSError:
        pass


def _play_launch(su, graphics):
    """A lingering shower of twinkling stars with a shimmer sound."""
    # Stars appear with their own shimmer sound and stay on, gently shimmering.
    _try_play(su, STAR_SOUND)
    for frame in range(_LAUNCH_FLASH_FRAMES):
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()
        for i, (sx, sy) in enumerate(_STARS):
            # Every star stays lit; its colour shimmers slowly between warm
            # yellow and magnolia so the field twinkles instead of blinking off.
            colour = _STAR_HOT if ((i + frame // 4) % 2 == 0) else _STAR_SOFT
            display.set_pixel(graphics, sx, sy, *colour)
        su.update(graphics)
        time.sleep_ms(FRAME_MS)


def run(su, graphics, kx, should_exit=None):
    """
    Run the Rocket Blast-off game until the player exits or it auto-sleeps.

    should_exit() is polled each frame (the boat+butterfly hold from main.py).
    Returns EXIT if the player toggled out, or SLEEP if the toy was left still
    (rocket grounded, no shaking) for STILL_SLEEP_MS.
    """
    rocketball = Rocket()
    last_active = time.ticks_ms()
    last_debug = time.ticks_ms()
    whoosh_played = False   # whoosh fires once per flight; re-armed on landing

    while True:
        if should_exit and should_exit():
            return EXIT

        raw = kx.read_xyz()
        shake = shake_amount(*raw)

        # Whoosh when a flight begins: the first shake after the rocket has been
        # resting on the ground. It plays once and won't repeat until the rocket
        # lands (or launches) and shaking starts again.
        if shake > 0.0 and not whoosh_played:
            _try_play(su, LAUNCH_SOUND)
            whoosh_played = True

        if rocketball.step(shake):
            _play_launch(su, graphics)
            rocketball = Rocket()          # fresh rocket drops back to the ground
            last_active = time.ticks_ms()
            last_debug = time.ticks_ms()
            whoosh_played = False          # re-arm the whoosh for the next flight
            continue

        # Back on the ground and not being shaken → the flight is over; re-arm
        # the whoosh so the next shake starts a fresh one.
        if rocketball.rx <= GROUND_RX and shake == 0.0:
            whoosh_played = False

        now = time.ticks_ms()

        # Tuning telemetry — raw g-force, derived shake, and rocket state.
        if DEBUG and time.ticks_diff(now, last_debug) >= _DEBUG_INTERVAL_MS:
            rx, ry, rz = raw
            print("[ROCKET] raw=({:+.2f},{:+.2f},{:+.2f})g  shake={:.2f}  "
                  "rx={:.1f}/{:.0f}  vy={:+.2f}".format(
                      rx, ry, rz, shake, rocketball.rx, LAUNCH_RX, rocketball.vy))
            last_debug = now

        if rocketball.is_active(shake):
            last_active = now
        elif time.ticks_diff(now, last_active) >= STILL_SLEEP_MS:
            return SLEEP

        _render(graphics, su, rocketball, shake)
        time.sleep_ms(FRAME_MS)
