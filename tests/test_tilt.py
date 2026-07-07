"""
Behavioural tests for the Tilt Game.

The physics core (TiltBall) is pure and hardware-free: it takes accelerometer
X/Y G-force each frame and updates ball position/velocity, bouncing off the
walls of the 16x16 display. run() wires it to the KX134, display and sound.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_tilt
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fake time module (installed before tilt is imported) ──────────────────────
class _FakeClock:
    STEP_MS = 33

    def __init__(self):
        self._ms = 0

    def reset(self):
        self._ms = 0

    def ticks_ms(self):
        return self._ms

    def ticks_diff(self, a, b):
        return a - b

    def sleep_ms(self, ms):
        self._ms += ms


_clock = _FakeClock()
_fake_time = types.ModuleType("time")
_fake_time.ticks_ms = _clock.ticks_ms
_fake_time.ticks_diff = _clock.ticks_diff
_fake_time.sleep_ms = _clock.sleep_ms
sys.modules["time"] = _fake_time

sys.modules.setdefault("machine", MagicMock())

from games import tilt  # noqa: E402


class TiltBallTest(unittest.TestCase):

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_ball_starts_at_centre(self):
        """A new ball sits at the centre of the 16x16 display."""
        ball = tilt.TiltBall()
        self.assertAlmostEqual(ball.x, tilt.CENTRE)
        self.assertAlmostEqual(ball.y, tilt.CENTRE)

    # ── Border: ball stays inside the 1px white frame ────────────────────────

    def test_ball_stays_inside_the_border(self):
        """Even slammed into a corner, the 2x2 ball never sits on the edge ring."""
        ball = tilt.TiltBall()
        for _ in range(200):
            ball.step(-1.0, -1.0)   # slam toward the origin corner
        # Top-left pixel of the block must be >= 1, and its far pixel <= 14.
        self.assertGreaterEqual(int(round(ball.x)), 1)
        self.assertGreaterEqual(int(round(ball.y)), 1)
        for _ in range(200):
            ball.step(1.0, 1.0)     # slam toward the far corner
        self.assertLessEqual(int(round(ball.x)) + tilt.BALL_SIZE - 1, 14)
        self.assertLessEqual(int(round(ball.y)) + tilt.BALL_SIZE - 1, 14)

    # ── Cycle 2: tilt accelerates the ball ────────────────────────────────────

    def test_positive_tilt_moves_ball(self):
        """A positive X/Y tilt builds velocity and moves the ball that way."""
        ball = tilt.TiltBall()
        ball.step(0.5, 0.5)   # tilt toward +x, +y
        self.assertGreater(ball.vx, 0.0)
        self.assertGreater(ball.vy, 0.0)
        self.assertGreater(ball.x, tilt.CENTRE)
        self.assertGreater(ball.y, tilt.CENTRE)

    def test_negative_tilt_moves_ball_other_way(self):
        """A negative tilt moves the ball toward the origin corner."""
        ball = tilt.TiltBall()
        ball.step(-0.5, -0.5)
        self.assertLess(ball.x, tilt.CENTRE)
        self.assertLess(ball.y, tilt.CENTRE)

    # ── Cycle 3: elastic wall bounce ─────────────────────────────────────────

    def test_ball_stays_within_bounds(self):
        """However hard it's driven, the ball never leaves the display."""
        ball = tilt.TiltBall()
        for _ in range(200):
            ball.step(1.0, 1.0)   # slam toward the far corner
            self.assertGreaterEqual(ball.x, tilt.MIN_POS)
            self.assertLessEqual(ball.x, tilt.MAX_POS)
            self.assertGreaterEqual(ball.y, tilt.MIN_POS)
            self.assertLessEqual(ball.y, tilt.MAX_POS)

    def test_bounce_reverses_velocity_and_is_reported(self):
        """Hitting the far wall flips vx from positive to negative, and step() reports it."""
        ball = tilt.TiltBall()
        bounced = False
        for _ in range(100):
            if ball.step(1.0, 0.0):
                bounced = True
                break
        self.assertTrue(bounced, "ball never bounced off the +x wall")
        self.assertLess(ball.vx, 0.0, "vx should reverse after hitting the +x wall")

    # ── Cycle 4: bounce loses energy ─────────────────────────────────────────

    def test_bounce_loses_energy(self):
        """The ball leaves a wall slower than it arrived (energy loss)."""
        ball = tilt.TiltBall(x=tilt.MAX_POS - 0.5, y=tilt.CENTRE)
        ball.vx = 2.0
        speed_in = abs(ball.vx)
        self.assertTrue(ball.step(0.0, 0.0), "expected a bounce this frame")
        self.assertLess(abs(ball.vx), speed_in)

    # ── Cycle 5: friction settles the ball ───────────────────────────────────

    def test_friction_slows_a_moving_ball(self):
        """With no tilt, a moving ball loses speed each frame (away from walls)."""
        ball = tilt.TiltBall(x=tilt.CENTRE, y=tilt.CENTRE)
        ball.vx = 1.0
        ball.step(0.0, 0.0)   # no tilt, no wall hit
        self.assertLess(ball.vx, 1.0)
        self.assertGreater(ball.vx, 0.0)   # still moving, just slower

    # ── Cycle 6: colour follows the tilt (roll) direction ────────────────────

    def test_colour_follows_tilt_direction(self):
        """Colour snaps to the dominant tilt axis (veneer-safe palette)."""
        ball = tilt.TiltBall()
        ball.step(1.0, 0.1)
        self.assertEqual(ball.colour(), tilt.RED)      # tilt up
        ball.step(-1.0, 0.1)
        self.assertEqual(ball.colour(), tilt.AQUA)     # tilt down
        ball.step(0.1, 1.0)
        self.assertEqual(ball.colour(), tilt.YELLOW)   # tilt right
        ball.step(0.1, -1.0)
        self.assertEqual(ball.colour(), tilt.GREEN)    # tilt left

    def test_colour_held_when_toy_is_level(self):
        """With no tilt (level toy), the colour holds — it does not reset."""
        ball = tilt.TiltBall()
        ball.step(0.0, -1.0)                # tilt left → green
        self.assertEqual(ball.colour(), tilt.GREEN)
        ball.step(0.0, 0.0)                 # level: no tilt
        self.assertEqual(ball.colour(), tilt.GREEN)   # stays green, not default red

    def test_colour_ignores_wall_rebound(self):
        """Rolling into a wall and settling keeps the tilt colour, not the rebound.

        Reproduces the reported bug: tilt left → green, but after the ball
        bounced off the wall and settled it used to flip to yellow.
        """
        ball = tilt.TiltBall(x=tilt.CENTRE, y=tilt.MIN_POS + 3)
        ball.step(0.0, -0.9)               # tilt left → green, rolling at the wall
        self.assertEqual(ball.colour(), tilt.GREEN)
        for _ in range(40):                # level off; ball bounces and settles
            ball.step(0.0, 0.0)
        self.assertEqual(ball.colour(), tilt.GREEN)   # still green after the rebound

    def test_colour_stays_while_held_into_wall(self):
        """Holding the tilt into a wall (ball micro-bouncing) keeps the colour."""
        ball = tilt.TiltBall(x=tilt.CENTRE, y=tilt.MIN_POS + 3)
        for _ in range(60):                # keep tilting left the whole time
            ball.step(0.0, -0.9)
        self.assertEqual(ball.colour(), tilt.GREEN)

    def test_colours_are_veneer_safe(self):
        """No banned colours: never purple (r>0,b>0,g==0) or faint plain blue."""
        for c in (tilt.RED, tilt.YELLOW, tilt.AQUA, tilt.GREEN):
            r, g, b = c
            self.assertFalse(r > 0 and b > 0 and g == 0, f"{c} looks purple")
            self.assertNotEqual(c, (0, 0, 255), "plain blue is too faint on the veneer")

    # ── Cycle 7: Tilt Activity (moving vs. still) ────────────────────────────

    def test_is_moving_reflects_speed(self):
        """is_moving() is True above the activity threshold, False when nearly still."""
        ball = tilt.TiltBall()
        ball.vx, ball.vy = 0.0, 0.0
        self.assertFalse(ball.is_moving())
        ball.vx, ball.vy = 1.0, 0.0
        self.assertTrue(ball.is_moving())

    # ── Cycle 13: only real impacts count as bounces ─────────────────────────

    def test_fast_impact_is_a_bounce(self):
        """A ball arriving at a wall with real speed reports a bounce."""
        ball = tilt.TiltBall(x=tilt.MAX_POS - 0.5, y=tilt.CENTRE)
        ball.vx = 2.0   # fast impact
        self.assertTrue(ball.step(0.0, 0.0))

    def test_resting_against_wall_is_not_a_bounce(self):
        """A ball barely pressing the wall (tiny speed) does not re-report bounces.

        This stops the bounce sound machine-gunning while the toy is held at a
        steep angle and the ball just rests against an edge.
        """
        ball = tilt.TiltBall(x=tilt.MAX_POS, y=tilt.CENTRE)
        ball.vx = 0.05   # barely creeping into the wall
        self.assertFalse(ball.step(0.0, 0.0))


class SensorOrientationTest(unittest.TestCase):
    """The KX134 is mounted rotated 90° vs the display; sensor_to_tilt fixes it.

    Observed on hardware (held flat, screen up):
      - tipping the RIGHT edge down reads raw_x < 0 and should roll the ball right
      - tipping the TOP edge down reads raw_y > 0 and should roll the ball up
    step(ax, ay): ax accelerates the ball vertically (+ = up), ay horizontally
    (+ = right).
    """

    def test_right_edge_down_rolls_ball_right(self):
        ax, ay = tilt.sensor_to_tilt(-1.0, 0.0)   # right edge down
        self.assertAlmostEqual(ax, 0.0)            # no vertical push
        self.assertGreater(ay, 0.0)                # rolls right

    def test_top_edge_down_rolls_ball_up(self):
        ax, ay = tilt.sensor_to_tilt(0.0, 1.0)    # top edge down
        self.assertGreater(ax, 0.0)                # rolls up
        self.assertAlmostEqual(ay, 0.0)            # no horizontal push

    def test_tiny_tilt_within_deadzone_is_ignored(self):
        """Noise/level-bias below the deadzone produces no acceleration (no drift)."""
        small = tilt.DEADZONE * 0.5
        self.assertEqual(tilt.sensor_to_tilt(small, -small), (0.0, 0.0))

    def test_tilt_beyond_deadzone_still_moves(self):
        """A real tilt past the deadzone still accelerates the ball."""
        beyond = tilt.DEADZONE + 0.1
        ax, ay = tilt.sensor_to_tilt(-beyond, 0.0)   # right edge down, past deadzone
        self.assertGreater(ay, 0.0)


def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g


def _make_kx(x=0.0, y=0.0):
    kx = MagicMock()
    kx.read_xy.return_value = (x, y)
    return kx


class _RecordingGraphics:
    """Graphics stub that records the colour drawn to each physical pixel."""
    def __init__(self):
        self._pen = (0, 0, 0)
        self.drawn = {}   # (px, py) -> (r, g, b)

    def create_pen(self, r, g, b):
        return (r, g, b)

    def set_pen(self, pen):
        self._pen = pen

    def clear(self):
        self.drawn = {}

    def pixel(self, px, py):
        self.drawn[(px, py)] = self._pen

    def update(self, *_):
        pass


class TiltRunTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su = MagicMock()
        self.graphics = _make_graphics()
        self._sound_patcher = patch.object(tilt, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._sound_patcher.stop()

    # ── Cycle 8: exit signal ends the game ───────────────────────────────────

    def test_run_returns_exit_when_signalled(self):
        """run() returns EXIT once should_exit() fires (yellow+red toggle)."""
        result = tilt.run(self.su, self.graphics, _make_kx(), should_exit=lambda: True)
        self.assertEqual(result, tilt.EXIT)

    # ── Border: a white ring is drawn around the edge each frame ─────────────

    def test_white_border_is_drawn(self):
        """Every edge pixel of the 16x16 display is drawn white."""
        g = _RecordingGraphics()
        tilt.run(self.su, g, _make_kx(), should_exit=self._exit_after(1))
        edges = [(0, i) for i in range(16)] + [(15, i) for i in range(16)] \
            + [(i, 0) for i in range(16)] + [(i, 15) for i in range(16)]
        for px in edges:
            self.assertEqual(g.drawn.get(px), tilt.WHITE, f"edge pixel {px} not white")

    # ── Cycle 9: bounce plays the bounce sound ───────────────────────────────

    def _exit_after(self, n):
        """A should_exit callable that returns True on the n-th call."""
        calls = [0]
        def check():
            calls[0] += 1
            return calls[0] > n
        return check

    def test_wall_bounce_plays_bounce_sound(self):
        """Driving the ball into a wall plays sounds/bounce.wav."""
        kx = _make_kx(x=1.0, y=0.0)   # slam toward the +x wall
        tilt.run(self.su, self.graphics, kx, should_exit=self._exit_after(60))
        self.mock_sound.play.assert_any_call(self.su, tilt.BOUNCE_SOUND)

    def test_missing_bounce_sound_is_ignored(self):
        """A missing bounce.wav (OSError) does not crash the game."""
        self.mock_sound.play.side_effect = OSError("no file")
        kx = _make_kx(x=1.0, y=0.0)
        result = tilt.run(self.su, self.graphics, kx, should_exit=self._exit_after(60))
        self.assertEqual(result, tilt.EXIT)

    # ── Cycle 10: ball renders as a 2x2 block ────────────────────────────────

    def test_ball_drawn_as_2x2_block(self):
        """One frame draws the ball's four pixels around the centre."""
        drawn = []
        with patch.object(tilt.display, "pixel",
                           side_effect=lambda _g, x, y: drawn.append((x, y))):
            tilt.run(self.su, self.graphics, _make_kx(), should_exit=self._exit_after(1))
        for px in [(7, 7), (8, 7), (7, 8), (8, 8)]:
            self.assertIn(px, drawn, f"ball pixel {px} was not drawn")

    # ── Cycle 11: fading trail ───────────────────────────────────────────────

    def test_ball_leaves_a_fading_trail(self):
        """A moving ball draws dimmed pixels behind it (a fading trail)."""
        drawn = []
        with patch.object(tilt.display, "pixel",
                           side_effect=lambda _g, x, y: drawn.append((x, y))):
            # Roll steadily in one direction for several frames.
            tilt.run(self.su, self.graphics, _make_kx(x=0.4),
                     should_exit=self._exit_after(12))

        # Trail means more distinct pixels light up than the 4 of the ball alone.
        self.assertGreater(len(set(drawn)), 4)

        # The trail is a dimmed version of the ball colour: a pen that is not
        # black, not the white border, and not a full-brightness cardinal.
        full = {tilt.RED, tilt.YELLOW, tilt.AQUA, tilt.GREEN, tilt.WHITE, (0, 0, 0)}
        dimmed = [p for p in (c.args for c in self.graphics.create_pen.call_args_list)
                  if p not in full and any(v > 0 for v in p)]
        self.assertTrue(dimmed, "no dimmed trail pixels found")

    # ── Cycle 12: settles to sleep when held still ───────────────────────────

    def test_run_returns_sleep_when_held_still(self):
        """With no tilt, a still ball eventually returns SLEEP for auto-sleep."""
        with patch.object(tilt, "STILL_SLEEP_MS", 200):   # a few frames, not 2 min
            result = tilt.run(self.su, self.graphics, _make_kx(0.0, 0.0),
                              should_exit=lambda: False)
        self.assertEqual(result, tilt.SLEEP)

    def test_active_play_does_not_sleep(self):
        """While the ball keeps moving (real play sloshes the tilt), no sleep."""
        kx = MagicMock()
        calls = [0]
        def read_xy():
            calls[0] += 1
            # Reverse the tilt every 10 frames so the ball sloshes across the
            # display, staying above the activity threshold like real play.
            return (0.6 if (calls[0] // 10) % 2 == 0 else -0.6, 0.0)
        kx.read_xy.side_effect = read_xy
        with patch.object(tilt, "STILL_SLEEP_MS", 200):
            result = tilt.run(self.su, self.graphics, kx,
                              should_exit=self._exit_after(60))
        self.assertEqual(result, tilt.EXIT)


if __name__ == "__main__":
    unittest.main()
