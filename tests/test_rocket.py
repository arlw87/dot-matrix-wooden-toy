"""
Behavioural tests for the rocket animation.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_rocket
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fake time module ──────────────────────────────────────────────────────────
# Must be installed before rocket_module is imported so the module binds our fake.

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

import animations.rocket as rocket_module  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g

def _make_su():
    return MagicMock()


# ── Test cases ────────────────────────────────────────────────────────────────

class RocketAnimationTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su       = _make_su()
        self.graphics = _make_graphics()
        # Belt-and-braces: patch rocket_module.time directly in case it was
        # imported before this test file set sys.modules["time"].
        self._time_patcher  = patch.object(rocket_module, "time", _fake_time)
        self._time_patcher.start()
        self._sound_patcher = patch.object(rocket_module, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._time_patcher.stop()
        self._sound_patcher.stop()

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_play_completes_returns_none(self):
        """play() with no interrupts completes both phases and returns None."""
        result = rocket_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 2: animation-phase interrupt ───────────────────────────────────

    def test_interrupt_during_animation_returns_button_name(self):
        """play() returns the button name when interrupted during animation."""
        calls = [0]
        def check():
            calls[0] += 1
            return "heart" if calls[0] >= 3 else None
        result = rocket_module.play(self.su, self.graphics, check_interrupt=check)
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
        result = rocket_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "star")

    # ── Cycle 4: sound plays at start ────────────────────────────────────────

    def test_sound_file_attempted_at_start(self):
        """play() calls sound.play with sounds/rocket.wav before animating."""
        rocket_module.play(self.su, self.graphics)
        self.mock_sound.play.assert_called_once_with(self.su, "sounds/rocket.wav")

    # ── Cycle 5: sound stops on animation interrupt ───────────────────────────

    def test_sound_stops_on_animation_interrupt(self):
        """sound.stop is called when interrupted during the animation phase."""
        rocket_module.play(self.su, self.graphics, check_interrupt=lambda: "flower")
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_not_stopped_on_hold_interrupt(self):
        """sound.stop is NOT called when interrupted during the Hold Phase."""
        calls = [0]
        def check():
            calls[0] += 1
            return "butterfly" if calls[0] > 10 else None
        rocket_module.play(self.su, self.graphics, check_interrupt=check)
        self.mock_sound.stop.assert_not_called()

    # ── Cycle 6: graceful handling of missing sound file ─────────────────────

    def test_animation_continues_if_sound_file_missing(self):
        """play() runs to completion even if sounds/rocket.wav raises OSError."""
        self.mock_sound.play.side_effect = OSError("file not found")
        result = rocket_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 7: green body pixels ───────────────────────────────────────────

    def test_green_body_pixels_used(self):
        """Rocket body pixels are green — g dominant over both r and b."""
        rocket_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        green_pens = [(r, g, b) for r, g, b in non_black if g > r and g > b]
        self.assertGreater(len(green_pens), 0,
            msg="No green pixels found — expected g > r and g > b for body")

    # ── Cycle 8: red nose + fin pixels ───────────────────────────────────────

    def test_red_nose_fin_pixels_used(self):
        """Nose cone and fin pixels are red — r > 150, g < 80, b < 80."""
        rocket_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        red_pens = [(r, g, b) for r, g, b in non_black
                    if r > 150 and g < 80 and b < 80]
        self.assertGreater(len(red_pens), 0,
            msg="No red pixels found — expected r > 150, g < 80, b < 80 for nose/fins")

    # ── Cycle 9: orange/yellow flame pixels ──────────────────────────────────

    def test_flame_pixels_used(self):
        """Flame pixels are orange/yellow — high r, significant g, very low b."""
        rocket_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        flame_pens = [(r, g, b) for r, g, b in non_black
                      if r > 200 and g > 70 and b < 50]
        self.assertGreater(len(flame_pens), 0,
            msg="No flame pixels found — expected r > 200, g > 70, b < 50")

    # ── Cycle 10: magnolia window pixels ─────────────────────────────────────

    def test_magnolia_window_pixels_used(self):
        """Window pixels are magnolia — all three channels high and roughly equal."""
        rocket_module.play(self.su, self.graphics)
        non_black = [c.args for c in self.graphics.create_pen.call_args_list
                     if c.args != (0, 0, 0)]
        magnolia_pens = [(r, g, b) for r, g, b in non_black
                         if r > 220 and g > 220 and b > 180]
        self.assertGreater(len(magnolia_pens), 0,
            msg="No magnolia pixels found — expected r > 220, g > 220, b > 180 for window")

    # ── Cycle 11: rocket travels from bottom to top ───────────────────────────

    def test_rocket_travels_bottom_to_top(self):
        """Over the animation, drawn pixels span from near x=0 (bottom) to near x=15 (top).

        display.pixel(graphics, x, y) uses x=0 for the bottom row and x=15 for
        the top row.  The rocket rises so early frames draw at low x and later
        frames draw at high x.
        """
        drawn = []
        with patch.object(
            rocket_module.display, "pixel",
            side_effect=lambda _g, x, y: drawn.append((x, y)),
        ):
            rocket_module.play(self.su, self.graphics)

        xs = [x for x, y in drawn]
        self.assertTrue(
            min(xs) <= 3,
            msg=f"Rocket never reached the bottom (min x={min(xs)})",
        )
        self.assertTrue(
            max(xs) >= 13,
            msg=f"Rocket never reached the top (max x={max(xs)})",
        )


# ── Button wiring tests ───────────────────────────────────────────────────────

class ButtonWiringTest(unittest.TestCase):

    def test_rocket_mapped_to_gpb0(self):
        """GPB0 (green button) maps to 'rocket'."""
        from lib import buttons
        self.assertIn("rocket", buttons.BUTTON_BITS)
        self.assertEqual(buttons.BUTTON_BITS["rocket"], 0)

    def test_fish_removed_from_button_bits(self):
        """'fish' is no longer in BUTTON_BITS — replaced by 'rocket'."""
        from lib import buttons
        self.assertNotIn("fish", buttons.BUTTON_BITS)

    def test_rocket_in_button_order(self):
        """'rocket' appears in BUTTON_ORDER."""
        from lib import buttons
        self.assertIn("rocket", buttons.BUTTON_ORDER)

    def test_fish_removed_from_button_order(self):
        """'fish' is no longer in BUTTON_ORDER."""
        from lib import buttons
        self.assertNotIn("fish", buttons.BUTTON_ORDER)


# ── Animation registry tests ──────────────────────────────────────────────────

class RegistryTest(unittest.TestCase):

    def test_rocket_in_animation_registry(self):
        """get_animation('rocket') returns the rocket module with a play() function."""
        from animations import get_animation
        anim = get_animation("rocket")
        self.assertIsNotNone(anim)
        self.assertTrue(hasattr(anim, "play"))

    def test_fish_removed_from_registry(self):
        """get_animation('fish') returns None — fish has been replaced by rocket."""
        from animations import get_animation
        self.assertIsNone(get_animation("fish"))


if __name__ == "__main__":
    unittest.main()
