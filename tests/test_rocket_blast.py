"""
Behavioural tests for the Rocket Blast-off game.

The physics core (Rocket) is pure and hardware-free: each frame it takes a
shake amount (how hard the toy is being shaken) and updates the rocket's
height/velocity. Shaking thrusts the rocket up; gravity pulls it back to the
ground; sustained shaking launches it. run() wires it to the KX134, display and
sound. Entered/exited by holding blue (boat) + pink (butterfly) for 5s.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_rocket_blast
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, call, patch

# ── Fake time module (installed before rocket_blast is imported) ──────────────
class _FakeClock:
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

from games import rocket_blast  # noqa: E402


class ShakeAmountTest(unittest.TestCase):
    """shake_amount() turns raw accelerometer G-force into a shake intensity."""

    def test_level_still_toy_reads_zero(self):
        """Held level and still (~1 g down on Z), the shake amount is ~0."""
        self.assertEqual(rocket_blast.shake_amount(0.0, 0.0, 1.0), 0.0)

    def test_small_wobble_within_deadzone_is_ignored(self):
        """Tiny sensor noise below the deadzone counts as no shake."""
        tiny = rocket_blast.SHAKE_DEADZONE * 0.5
        self.assertEqual(rocket_blast.shake_amount(0.0, 0.0, 1.0 + tiny), 0.0)

    def test_vigorous_shake_reads_positive(self):
        """A big acceleration spike (magnitude far from 1 g) reads as shaking."""
        self.assertGreater(rocket_blast.shake_amount(3.0, 0.0, 1.0), 0.0)

    def test_shake_is_never_negative(self):
        """Even a below-gravity dip (free-fall-ish) returns a non-negative shake."""
        self.assertGreaterEqual(rocket_blast.shake_amount(0.0, 0.0, 0.0), 0.0)


class RocketTest(unittest.TestCase):

    def test_rocket_starts_on_the_ground(self):
        """A new rocket sits on the ground, not moving."""
        r = rocket_blast.Rocket()
        self.assertAlmostEqual(r.rx, rocket_blast.GROUND_RX)
        self.assertAlmostEqual(r.vy, 0.0)
        self.assertFalse(r.launched)

    def test_shaking_raises_the_rocket(self):
        """Shaking for several frames lifts the rocket above the ground."""
        r = rocket_blast.Rocket()
        for _ in range(10):
            r.step(2.0)
        self.assertGreater(r.rx, rocket_blast.GROUND_RX)

    def test_no_shake_lets_the_rocket_fall_back(self):
        """A rocket that has risen comes back down and settles once shaking stops."""
        r = rocket_blast.Rocket()
        for _ in range(6):
            r.step(2.0)             # give it a shove upward
        peak = r.rx
        for _ in range(200):
            r.step(0.0)             # stop shaking
            peak = max(peak, r.rx)  # it may coast up a little before falling
        self.assertLess(r.rx, peak)                                   # came back down
        self.assertAlmostEqual(r.rx, rocket_blast.GROUND_RX, delta=0.5)  # settled

    def test_rocket_never_sinks_below_the_ground(self):
        """With no shaking, the rocket rests on the ground and does not tunnel down."""
        r = rocket_blast.Rocket()
        for _ in range(50):
            r.step(0.0)
        self.assertGreaterEqual(r.rx, rocket_blast.GROUND_RX)

    def test_sustained_shaking_launches_the_rocket(self):
        """Keep shaking hard and the rocket eventually launches off the top."""
        r = rocket_blast.Rocket()
        launched = False
        for _ in range(200):
            if r.step(3.0):
                launched = True
                break
        self.assertTrue(launched, "hard sustained shaking never launched the rocket")
        self.assertTrue(r.launched)
        self.assertGreaterEqual(r.rx, rocket_blast.LAUNCH_RX)

    def test_gentle_shake_alone_does_not_launch(self):
        """A weak shake below the thrust needed to beat gravity never launches."""
        r = rocket_blast.Rocket()
        launched = False
        for _ in range(200):
            # Just above the deadzone — enough to register, not enough to climb.
            if r.step(rocket_blast.SHAKE_DEADZONE):
                launched = True
                break
        self.assertFalse(launched, "a barely-there shake should not reach orbit")

    def test_ascend_speed_is_capped_above_max_shake(self):
        """Shaking harder than MAX_SHAKE climbs no faster than a MAX_SHAKE shake."""
        capped = rocket_blast.Rocket()
        frantic = rocket_blast.Rocket()
        for _ in range(20):
            capped.step(rocket_blast.MAX_SHAKE)
            frantic.step(rocket_blast.MAX_SHAKE * 3)   # way harder
            self.assertAlmostEqual(frantic.vy, capped.vy)
            self.assertAlmostEqual(frantic.rx, capped.rx)

    def test_below_the_cap_a_harder_shake_is_faster(self):
        """Under the cap, a stronger shake still builds more speed."""
        soft = rocket_blast.Rocket()
        hard = rocket_blast.Rocket()
        for _ in range(5):
            soft.step(rocket_blast.MAX_SHAKE * 0.5)
            hard.step(rocket_blast.MAX_SHAKE)
        self.assertGreater(hard.vy, soft.vy)

    def test_is_active_while_shaking_or_airborne(self):
        """The rocket counts as active (resets sleep) while shaken or off the ground."""
        r = rocket_blast.Rocket()
        self.assertFalse(r.is_active(0.0))          # grounded, not shaken → idle
        self.assertTrue(r.is_active(2.0))           # being shaken → active
        for _ in range(10):
            r.step(2.0)
        self.assertTrue(r.is_active(0.0))           # airborne → active even if still


def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g


def _make_kx(x=0.0, y=0.0, z=1.0):
    kx = MagicMock()
    kx.read_xyz.return_value = (x, y, z)
    return kx


class RocketRunTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su = MagicMock()
        self.graphics = _make_graphics()
        self._sound_patcher = patch.object(rocket_blast, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()
        # The real star shower lingers ~5 s (160 frames); shrink it here so the
        # launch tests don't render thousands of mock frames. Its true duration
        # lives in the _LAUNCH_FLASH_FRAMES constant, not in these tests.
        self._flash_patcher = patch.object(rocket_blast, "_LAUNCH_FLASH_FRAMES", 3)
        self._flash_patcher.start()
        # Keep the tuning telemetry out of the test output.
        self._debug_patcher = patch.object(rocket_blast, "DEBUG", False)
        self._debug_patcher.start()

    def tearDown(self):
        self._debug_patcher.stop()
        self._flash_patcher.stop()
        self._sound_patcher.stop()

    def _exit_after(self, n):
        """A should_exit callable that returns True on the (n+1)-th call."""
        calls = [0]
        def check():
            calls[0] += 1
            return calls[0] > n
        return check

    def test_run_returns_exit_when_signalled(self):
        """run() returns EXIT once should_exit() fires (boat+butterfly toggle)."""
        result = rocket_blast.run(self.su, self.graphics, _make_kx(),
                                  should_exit=lambda: True)
        self.assertEqual(result, rocket_blast.EXIT)

    def _whoosh_count(self):
        """How many times the whoosh (rocket.wav) was played."""
        return sum(1 for c in self.mock_sound.play.call_args_list
                   if c == call(self.su, rocket_blast.LAUNCH_SOUND))

    def test_shaking_plays_the_whoosh_sound(self):
        """Shaking the toy plays the rocket whoosh."""
        kx = _make_kx(x=3.0)   # constant hard shake every frame
        rocket_blast.run(self.su, self.graphics, kx,
                         should_exit=self._exit_after(300))
        self.mock_sound.play.assert_any_call(self.su, rocket_blast.LAUNCH_SOUND)

    def test_whoosh_plays_once_per_flight_and_rearms_after_landing(self):
        """The whoosh plays once while shaking, then again for a fresh flight."""
        # Shake for a burst (rises), rest long enough to land, then shake again.
        script = ([(2.0, 0.0, 0.0)] * 8
                  + [(0.0, 0.0, 1.0)] * 80
                  + [(2.0, 0.0, 0.0)] * 8)
        it = iter(script)
        kx = MagicMock()
        kx.read_xyz.side_effect = lambda: next(it, (0.0, 0.0, 1.0))
        # Keep it from launching so we isolate the ground→shake re-arm behaviour.
        with patch.object(rocket_blast, "LAUNCH_RX", 1000.0):
            rocket_blast.run(self.su, self.graphics, kx,
                             should_exit=self._exit_after(len(script) + 5))
        self.assertEqual(self._whoosh_count(), 2,
                         "whoosh should fire once per shake-flight, not per frame")

    def test_launch_plays_the_star_sound(self):
        """When the launch stars appear they play their own shimmer sound."""
        kx = _make_kx(x=3.0)
        rocket_blast.run(self.su, self.graphics, kx,
                         should_exit=self._exit_after(300))
        self.mock_sound.play.assert_any_call(self.su, rocket_blast.STAR_SOUND)

    def test_missing_launch_sound_is_ignored(self):
        """A missing rocket.wav (OSError) does not crash the game."""
        self.mock_sound.play.side_effect = OSError("no file")
        kx = _make_kx(x=3.0)
        result = rocket_blast.run(self.su, self.graphics, kx,
                                  should_exit=self._exit_after(300))
        self.assertEqual(result, rocket_blast.EXIT)

    def test_run_returns_sleep_when_left_still(self):
        """Left on the ground with no shaking, the game returns SLEEP."""
        with patch.object(rocket_blast, "STILL_SLEEP_MS", 200):
            result = rocket_blast.run(self.su, self.graphics, _make_kx(),
                                      should_exit=lambda: False)
        self.assertEqual(result, rocket_blast.SLEEP)

    def test_active_shaking_does_not_sleep(self):
        """While the toy is being shaken, the game does not fall asleep."""
        kx = _make_kx(x=3.0)
        with patch.object(rocket_blast, "STILL_SLEEP_MS", 200):
            result = rocket_blast.run(self.su, self.graphics, kx,
                                      should_exit=self._exit_after(60))
        self.assertEqual(result, rocket_blast.EXIT)

    def test_rocket_pixels_are_drawn(self):
        """Each frame draws the rocket sprite (some pixels light up)."""
        drawn = []
        with patch.object(rocket_blast, "_px",
                          side_effect=lambda g, x, y, r, gr, b: drawn.append((x, y))):
            rocket_blast.run(self.su, self.graphics, _make_kx(),
                             should_exit=self._exit_after(1))
        self.assertTrue(drawn, "no rocket pixels were drawn")


if __name__ == "__main__":
    unittest.main()
