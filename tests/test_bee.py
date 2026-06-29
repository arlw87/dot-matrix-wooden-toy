"""
Behavioural tests for the bee animation.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_bee
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fake time module ──────────────────────────────────────────────────────────
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

sys.modules.setdefault("machine", MagicMock())

# ── Import module under test ──────────────────────────────────────────────────
import animations.bee as bee_module  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_graphics():
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g

def _make_su():
    return MagicMock()


# ── Tests ─────────────────────────────────────────────────────────────────────
class BeeAnimationTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su       = _make_su()
        self.graphics = _make_graphics()
        self._sound_patcher = patch.object(bee_module, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._sound_patcher.stop()

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_play_completes_returns_none(self):
        """play() with no interrupts completes both phases and returns None."""
        result = bee_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 2: animation-phase interrupt ───────────────────────────────────

    def test_interrupt_during_animation_returns_button_name(self):
        """play() returns the button name when interrupted during the animation."""
        calls = [0]
        def check():
            calls[0] += 1
            return "heart" if calls[0] >= 3 else None
        result = bee_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "heart")

    # ── Cycle 3: hold-phase interrupt ────────────────────────────────────────

    def test_interrupt_during_hold_returns_button_name(self):
        """play() returns the button name when interrupted during the Hold Phase.

        With STEP_MS=500 the 5-second animation loop runs exactly 10 times.
        Call #11 is the first check inside the Hold Phase.
        """
        calls = [0]
        def check():
            calls[0] += 1
            return "star" if calls[0] > 10 else None
        result = bee_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "star")

    # ── Cycle 4: sound plays at start ────────────────────────────────────────

    def test_sound_file_attempted_at_start(self):
        """play() calls sound.play with sounds/bee.wav before animating."""
        bee_module.play(self.su, self.graphics)
        self.mock_sound.play.assert_called_once_with(self.su, "sounds/bee.wav")

    # ── Cycle 5: sound stops on animation interrupt ───────────────────────────

    def test_sound_stops_on_animation_interrupt(self):
        """sound.stop is called when interrupted during the animation phase."""
        bee_module.play(self.su, self.graphics, check_interrupt=lambda: "flower")
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_not_stopped_on_hold_interrupt(self):
        """sound.stop is NOT called when interrupted during the Hold Phase."""
        calls = [0]
        def check():
            calls[0] += 1
            return "rocket" if calls[0] > 10 else None
        bee_module.play(self.su, self.graphics, check_interrupt=check)
        self.mock_sound.stop.assert_not_called()

    # ── Cycle 6: missing sound file ──────────────────────────────────────────

    def test_animation_continues_if_sound_file_missing(self):
        """play() runs to completion even if sounds/bee.wav raises OSError."""
        self.mock_sound.play.side_effect = OSError("file not found")
        result = bee_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 7: orange and dark stripe pixels ───────────────────────────────

    def test_orange_and_dark_stripe_pixels_used(self):
        """Body uses both orange pixels (r>200, g>50, b<50) and dark stripe
        pixels (all channels < 100) — confirming alternating horizontal stripes.
        Sky blue background (b>150, g>100, r<100) must not be miscounted."""
        bee_module.play(self.su, self.graphics)
        all_pens = [c.args for c in self.graphics.create_pen.call_args_list]

        orange = [(r,g,b) for r,g,b in all_pens if r > 200 and g > 50 and b < 50]
        dark   = [(r,g,b) for r,g,b in all_pens if r < 100 and g < 100 and b < 100]

        self.assertGreater(len(orange), 0, "No orange stripe pixels found")
        self.assertGreater(len(dark),   0, "No dark stripe pixels found")

    # ── Cycle 8: white wing pixels ────────────────────────────────────────────

    def test_white_wing_pixels_used(self):
        """Wings are drawn in white (all channels > 200)."""
        bee_module.play(self.su, self.graphics)
        all_pens = [c.args for c in self.graphics.create_pen.call_args_list]
        white = [(r,g,b) for r,g,b in all_pens if r > 200 and g > 200 and b > 200]
        self.assertGreater(len(white), 0, "No white wing pixels found")

    # ── Cycle 9: vertical oscillation range ──────────────────────────────────

    def test_bee_spans_vertical_range(self):
        """Over the animation, the bee reaches both near the top (y<4) and
        near the bottom (y>11), confirming vertical oscillation."""
        drawn = []
        with patch.object(
            bee_module.display, "pixel",
            side_effect=lambda _g, x, y: drawn.append((x, y)),
        ):
            bee_module.play(self.su, self.graphics)

        ys = [y for x, y in drawn]
        self.assertTrue(min(ys) < 4,  f"Bee never reached top (min y={min(ys)})")
        self.assertTrue(max(ys) > 11, f"Bee never reached bottom (max y={max(ys)})")


# ── Button wiring tests ───────────────────────────────────────────────────────
class ButtonWiringTest(unittest.TestCase):

    def test_bee_mapped_to_gpb4(self):
        """GPB4 maps to 'bee', replacing 'flower'."""
        from lib import buttons
        self.assertIn("bee", buttons.BUTTON_BITS)
        self.assertEqual(buttons.BUTTON_BITS["bee"], 4)
        self.assertNotIn("flower", buttons.BUTTON_BITS)

    def test_bee_in_button_order(self):
        """'bee' appears in BUTTON_ORDER; 'flower' does not."""
        from lib import buttons
        self.assertIn("bee", buttons.BUTTON_ORDER)
        self.assertNotIn("flower", buttons.BUTTON_ORDER)


# ── Animation registry tests ──────────────────────────────────────────────────
class RegistryTest(unittest.TestCase):

    def test_bee_in_animation_registry(self):
        """get_animation('bee') returns the bee module."""
        from animations import get_animation
        anim = get_animation("bee")
        self.assertIsNotNone(anim)
        self.assertTrue(hasattr(anim, "play"))

    def test_flower_removed_from_registry(self):
        """get_animation('flower') returns None — replaced by bee."""
        from animations import get_animation
        self.assertIsNone(get_animation("flower"))


if __name__ == "__main__":
    unittest.main()
