"""
Behavioural tests for the boat animation.
Run from the project root:  python3 -m unittest tests.test_boat
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fake time module ──────────────────────────────────────────────────────────
# Must be installed before boat_module is imported so the module binds our fake.

class _FakeClock:
    STEP_MS = 500

    def __init__(self):
        self._ms = 0

    def reset(self):
        self._ms = 0

    def ticks_ms(self):
        return self._ms

    def ticks_diff(self, a, b):
        return a - b

    def sleep_ms(self, _ms):
        self._ms += self.STEP_MS


_clock = _FakeClock()

_fake_time = types.ModuleType("time")
_fake_time.ticks_ms   = _clock.ticks_ms
_fake_time.ticks_diff = _clock.ticks_diff
_fake_time.sleep_ms   = _clock.sleep_ms
sys.modules["time"] = _fake_time

# ── MicroPython hardware stub ─────────────────────────────────────────────────
sys.modules.setdefault("machine", MagicMock())

# ── Import module under test ──────────────────────────────────────────────────
import animations.boat as boat_module  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g

def _make_su():
    return MagicMock()


# ── Test cases ────────────────────────────────────────────────────────────────

class BoatAnimationTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su       = _make_su()
        self.graphics = _make_graphics()
        self._time_patcher  = patch.object(boat_module, "time", _fake_time)
        self._time_patcher.start()
        self._sound_patcher = patch.object(boat_module, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._time_patcher.stop()
        self._sound_patcher.stop()

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_play_completes_returns_none(self):
        """play() with no interrupts completes both phases and returns None."""
        result = boat_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 2: animation-phase interrupt ───────────────────────────────────

    def test_interrupt_during_animation_returns_button_name(self):
        """play() returns the button name when interrupted during animation."""
        calls = [0]
        def check():
            calls[0] += 1
            return "heart" if calls[0] >= 3 else None
        result = boat_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "heart")

    # ── Cycle 3: hold-phase interrupt ────────────────────────────────────────

    def test_interrupt_during_hold_returns_button_name(self):
        """play() returns the button name when interrupted during the Hold Phase.

        With STEP_MS=500 the 5-second animation loop runs exactly 10 times.
        Call #11 is therefore the first check inside the Hold Phase.
        """
        calls = [0]
        def check():
            calls[0] += 1
            return "star" if calls[0] > 10 else None
        result = boat_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "star")

    # ── Cycle 4: sound plays at start ────────────────────────────────────────

    def test_sound_file_attempted_at_start(self):
        """play() calls sound.play with sounds/boat.wav before animating."""
        boat_module.play(self.su, self.graphics)
        self.mock_sound.play.assert_called_once_with(self.su, "sounds/boat.wav")

    # ── Cycle 5: sound stops on interrupt ────────────────────────────────────

    def test_sound_stops_on_animation_interrupt(self):
        """sound.stop is called when interrupted during the animation phase."""
        boat_module.play(self.su, self.graphics, check_interrupt=lambda: "flower")
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_stops_on_hold_interrupt(self):
        """sound.stop is called when interrupted during the Hold Phase."""
        calls = [0]
        def check():
            calls[0] += 1
            return "butterfly" if calls[0] > 10 else None
        boat_module.play(self.su, self.graphics, check_interrupt=check)
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_stops_on_completion(self):
        """sound.stop is called when the animation completes normally."""
        boat_module.play(self.su, self.graphics)
        self.mock_sound.stop.assert_called_once_with(self.su)

    # ── Cycle 6: graceful handling of missing sound file ─────────────────────

    def test_animation_continues_if_sound_file_missing(self):
        """play() runs to completion even if sounds/boat.wav raises OSError."""
        self.mock_sound.play.side_effect = OSError("file not found")
        result = boat_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 7: orange hull pixels ──────────────────────────────────────────

    def test_orange_hull_pixels_used(self):
        """Hull pixels are orange — r dominant, g moderate, b very low."""
        boat_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        orange_pens = [(r, g, b) for r, g, b in non_black
                       if r > 130 and r > g * 2 and b < 50]
        self.assertGreater(len(orange_pens), 0,
            msg="No orange pixels found — expected r dominant for hull")

    # ── Cycle 8: white wheelhouse pixels ─────────────────────────────────────

    def test_white_cabin_pixels_used(self):
        """Wheelhouse pixels are near-white — all three channels above 230."""
        boat_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        white_pens = [(r, g, b) for r, g, b in non_black
                      if r > 230 and g > 230 and b > 230]
        self.assertGreater(len(white_pens), 0,
            msg="No white pixels found — expected near-white for wheelhouse")

    # ── Cycle 9: blue water pixels ───────────────────────────────────────────

    def test_blue_water_pixels_used(self):
        """Water pixels are blue — b dominant over both r and g."""
        boat_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        blue_pens = [(r, g, b) for r, g, b in non_black
                     if b > r and b > g and b > 100]
        self.assertGreater(len(blue_pens), 0,
            msg="No blue pixels found — expected b dominant for water")

    # ── Cycle 10: water drawn at bottom rows ─────────────────────────────────

    def test_water_drawn_at_bottom_rows(self):
        """Water is always drawn at x=0 (depth) and x=1 (surface)."""
        drawn = []
        with patch.object(boat_module.display, "pixel",
                          side_effect=lambda g, x, y: drawn.append((x, y))):
            boat_module.play(self.su, self.graphics)
        xs = {x for x, y in drawn}
        self.assertIn(0, xs, msg="No pixels at x=0 — expected water depth row")
        self.assertIn(1, xs, msg="No pixels at x=1 — expected water surface row")

    # ── Cycle 11: boat drifts left to right ──────────────────────────────────

    def test_boat_drifts_left_to_right(self):
        """The max visible y (column) increases from first to last frame.

        drift starts at -13 (bow entering from left, hull visible at y≈1-2)
        and ends at +1 (boat settled to the right, hull visible at y≈2-15).
        """
        frames = []
        current = []

        def fake_pixel(g, x, y):
            current.append((x, y))

        def fake_update(g):
            if current:
                frames.append(list(current))
                current.clear()

        with patch.object(boat_module.display, "pixel", side_effect=fake_pixel):
            self.su.update.side_effect = fake_update
            boat_module.play(self.su, self.graphics)

        self.assertGreaterEqual(len(frames), 2, msg="Expected at least 2 frames")
        # Exclude water rows (x=0, x=1) which always span the full width
        first_max_y = max(y for x, y in frames[0]  if x >= 2)
        last_max_y  = max(y for x, y in frames[-1] if x >= 2)
        self.assertGreater(last_max_y, first_max_y,
            msg=f"Boat should drift right: first frame max_y={first_max_y}, "
                f"last frame max_y={last_max_y}")


# ── Button wiring tests ───────────────────────────────────────────────────────

class ButtonWiringTest(unittest.TestCase):

    def test_boat_mapped_to_gpb1(self):
        """GPB1 (blue button) maps to 'boat'."""
        from lib import buttons
        self.assertIn("boat", buttons.BUTTON_BITS)
        self.assertEqual(buttons.BUTTON_BITS["boat"], 1)

    def test_boot_removed_from_button_bits(self):
        """'boot' is no longer in BUTTON_BITS — replaced by 'boat'."""
        from lib import buttons
        self.assertNotIn("boot", buttons.BUTTON_BITS)

    def test_boat_in_button_order(self):
        """'boat' appears in BUTTON_ORDER."""
        from lib import buttons
        self.assertIn("boat", buttons.BUTTON_ORDER)

    def test_boot_removed_from_button_order(self):
        """'boot' is no longer in BUTTON_ORDER."""
        from lib import buttons
        self.assertNotIn("boot", buttons.BUTTON_ORDER)


# ── Animation registry tests ──────────────────────────────────────────────────

class RegistryTest(unittest.TestCase):

    def test_boat_in_animation_registry(self):
        """get_animation('boat') returns the boat module with a play() function."""
        from animations import get_animation
        anim = get_animation("boat")
        self.assertIsNotNone(anim)
        self.assertTrue(hasattr(anim, "play"))

    def test_boot_removed_from_registry(self):
        """get_animation('boot') returns None — boot button replaced by boat."""
        from animations import get_animation
        self.assertIsNone(get_animation("boot"))


if __name__ == "__main__":
    unittest.main()
