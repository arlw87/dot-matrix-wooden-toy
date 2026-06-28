"""
Behavioural tests for the fish animation.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_fish
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fake time module ──────────────────────────────────────────────────────────
# Must be installed before fish_module is imported so the module binds our fake.

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
# lib/buttons.py imports 'machine' which only exists on hardware.

sys.modules.setdefault("machine", MagicMock())

# ── Import module under test ──────────────────────────────────────────────────

import animations.fish as fish_module  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g

def _make_su():
    return MagicMock()


# ── Test cases ────────────────────────────────────────────────────────────────

class FishAnimationTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su       = _make_su()
        self.graphics = _make_graphics()
        self._sound_patcher = patch.object(fish_module, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._sound_patcher.stop()

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_play_completes_returns_none(self):
        """play() with no interrupts completes both phases and returns None."""
        result = fish_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 2: animation-phase interrupt ───────────────────────────────────

    def test_interrupt_during_animation_returns_button_name(self):
        """play() returns the button name when interrupted during animation."""
        calls = [0]
        def check():
            calls[0] += 1
            return "heart" if calls[0] >= 3 else None
        result = fish_module.play(self.su, self.graphics, check_interrupt=check)
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
        result = fish_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "star")

    # ── Cycle 4: sound plays at start ────────────────────────────────────────

    def test_sound_file_attempted_at_start(self):
        """play() calls sound.play with sounds/fish.wav before animating."""
        fish_module.play(self.su, self.graphics)
        self.mock_sound.play.assert_called_once_with(self.su, "sounds/fish.wav")

    # ── Cycle 5: sound stops on interrupt ────────────────────────────────────

    def test_sound_stops_on_animation_interrupt(self):
        """sound.stop is called when interrupted during the animation phase."""
        fish_module.play(self.su, self.graphics, check_interrupt=lambda: "flower")
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_not_stopped_on_hold_interrupt(self):
        """sound.stop is NOT called when interrupted during the Hold Phase."""
        calls = [0]
        def check():
            calls[0] += 1
            return "butterfly" if calls[0] > 10 else None
        fish_module.play(self.su, self.graphics, check_interrupt=check)
        self.mock_sound.stop.assert_not_called()

    # ── Cycle 6: graceful handling of missing sound file ─────────────────────

    def test_animation_continues_if_sound_file_missing(self):
        """play() runs to completion even if sounds/fish.wav raises OSError."""
        self.mock_sound.play.side_effect = OSError("file not found")
        result = fish_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 7: purple pixels ───────────────────────────────────────────────

    def test_purple_pixels_used(self):
        """Fish body pixels are purple — non-black pens have b > g and r > g."""
        fish_module.play(self.su, self.graphics)
        non_black = [
            c.args for c in self.graphics.create_pen.call_args_list
            if c.args != (0, 0, 0)
        ]
        purple_pens = [
            (r, g, b) for r, g, b in non_black
            if b > g and r > g
        ]
        self.assertGreater(
            len(purple_pens), 0,
            msg="No purple pixels found — expected b > g and r > g for fish body",
        )

    # ── Cycle 8: fish crosses the display horizontally ───────────────────────

    def test_fish_moves_across_horizontal_range(self):
        """Over the animation, pixels span from y < 5 to y > 10 (fish swims right→left)."""
        drawn = []
        with patch.object(
            fish_module.display, "pixel",
            side_effect=lambda _g, x, y: drawn.append((x, y)),
        ):
            fish_module.play(self.su, self.graphics)

        ys = [y for x, y in drawn]
        self.assertTrue(
            min(ys) < 5,
            msg=f"Fish never reached the left side (min y = {min(ys)})",
        )
        self.assertTrue(
            max(ys) > 10,
            msg=f"Fish never reached the right side (max y = {max(ys)})",
        )


# ── Button wiring tests ───────────────────────────────────────────────────────

class ButtonWiringTest(unittest.TestCase):

    def test_fish_mapped_to_gpb2(self):
        """GPB2 maps to 'fish', not 'moon'."""
        from lib import buttons
        self.assertIn("fish", buttons.BUTTON_BITS)
        self.assertEqual(buttons.BUTTON_BITS["fish"], 2)
        self.assertNotIn("moon", buttons.BUTTON_BITS)

    def test_fish_in_button_order(self):
        """'fish' appears in BUTTON_ORDER; 'moon' does not."""
        from lib import buttons
        self.assertIn("fish", buttons.BUTTON_ORDER)
        self.assertNotIn("moon", buttons.BUTTON_ORDER)


# ── Animation registry tests ──────────────────────────────────────────────────

class RegistryTest(unittest.TestCase):

    def test_fish_in_animation_registry(self):
        """get_animation('fish') returns the fish module."""
        from animations import get_animation
        anim = get_animation("fish")
        self.assertIsNotNone(anim)
        self.assertTrue(hasattr(anim, "play"))

    def test_moon_removed_from_registry(self):
        """get_animation('moon') returns None — moon has been replaced by fish."""
        from animations import get_animation
        self.assertIsNone(get_animation("moon"))


if __name__ == "__main__":
    unittest.main()
