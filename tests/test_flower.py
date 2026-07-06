"""
Behavioural tests for the redesigned flower animation.

Runs on desktop CPython with hardware stubs — no Raspberry Pi required.
Run from the project root:  python -m pytest tests/test_flower.py  (or unittest)
"""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ── 1. Fake time module ───────────────────────────────────────────────────────
# MicroPython exposes ticks_ms / ticks_diff / sleep_ms; CPython does not.
# Each sleep_ms call advances the clock by STEP_MS so 5 s loops finish fast.

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

# ── 2. Import the module under test ──────────────────────────────────────────
# Must happen AFTER time is replaced so the module binds our fake.

import animations.flower as flower_module  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_graphics():
    """Graphics stub that returns (r, g, b) tuples from create_pen for inspection."""
    g = MagicMock()
    g.create_pen.side_effect = lambda r, green, b: (r, green, b)
    return g


def _make_su():
    return MagicMock()


# ── Test cases ────────────────────────────────────────────────────────────────

class FlowerAnimationTest(unittest.TestCase):

    def setUp(self):
        _clock.reset()
        self.su       = _make_su()
        self.graphics = _make_graphics()
        # Replace flower_module.sound with a fresh mock each test
        self._sound_patcher = patch.object(flower_module, "sound", MagicMock())
        self.mock_sound = self._sound_patcher.start()

    def tearDown(self):
        self._sound_patcher.stop()

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_play_completes_returns_none(self):
        """play() with no interrupts completes both phases and returns None."""
        result = flower_module.play(self.su, self.graphics)
        self.assertIsNone(result)

    # ── Cycle 2: animation-phase interrupt ───────────────────────────────────

    def test_interrupt_during_animation_returns_button_name(self):
        """play() returns the button name when interrupted during animation."""
        calls = [0]
        def check():
            calls[0] += 1
            return "moon" if calls[0] >= 3 else None
        result = flower_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "moon")

    # ── Cycle 3: hold-phase interrupt ────────────────────────────────────────

    def test_interrupt_during_hold_returns_button_name(self):
        """play() returns the button name when interrupted during the Hold Phase.

        With STEP_MS=500 the animation loop runs exactly 10 times (0→4500 ms).
        Call #11 is therefore the first check inside the Hold Phase.
        """
        calls = [0]
        def check():
            calls[0] += 1
            return "heart" if calls[0] > 10 else None
        result = flower_module.play(self.su, self.graphics, check_interrupt=check)
        self.assertEqual(result, "heart")

    # ── Cycle 4: sound plays at start ────────────────────────────────────────

    def test_sound_file_played_at_start(self):
        """play() starts sounds/flower.wav before the animation loop."""
        flower_module.play(self.su, self.graphics)
        self.mock_sound.play.assert_called_once_with(self.su, "sounds/flower.wav")

    # ── Cycle 5: sound stops on interrupt ────────────────────────────────────

    def test_sound_stops_on_animation_phase_interrupt(self):
        """sound.stop is called when interrupted during the animation phase."""
        flower_module.play(self.su, self.graphics, check_interrupt=lambda: "star")
        self.mock_sound.stop.assert_called_once_with(self.su)

    def test_sound_not_stopped_on_hold_phase_interrupt(self):
        """sound.stop is NOT called when interrupted during the Hold Phase."""
        calls = [0]
        def check():
            calls[0] += 1
            return "butterfly" if calls[0] > 10 else None
        flower_module.play(self.su, self.graphics, check_interrupt=check)
        self.mock_sound.stop.assert_not_called()

    # ── Cycle 6: no green pixels ─────────────────────────────────────────────

    def test_no_green_pixels_used(self):
        """Every non-black pen must have r >= 200 (warm colours only — no green)."""
        flower_module.play(self.su, self.graphics)
        for c in self.graphics.create_pen.call_args_list:
            r, g, b = c.args
            if (r, g, b) != (0, 0, 0):
                self.assertGreaterEqual(
                    r, 200,
                    msg=f"Green-dominant colour used: create_pen({r}, {g}, {b})",
                )

    # ── Cycle 7: blooms from centre, not from bottom ─────────────────────────

    def test_blooms_from_centre(self):
        """Pixels appear near the centre and the overall centroid stays near (7.5, 7.5).

        Petals radiate in all directions so some reach the edges — that is correct.
        What matters is that the bloom is centred, not bottom-anchored like a stem.
        """
        drawn = []
        with patch.object(
            flower_module.display, "pixel",
            side_effect=lambda _g, x, y: drawn.append((x, y)),
        ):
            flower_module.play(self.su, self.graphics)

        # Must have pixels in the centre 6×6 region
        centre_hits = [(x, y) for x, y in drawn if 5 <= x <= 10 and 5 <= y <= 10]
        self.assertGreater(len(centre_hits), 0, "No pixels drawn in centre region")

        # Centroid must be near the display centre — a stem would pull it low
        avg_x = sum(x for x, y in drawn) / len(drawn)
        avg_y = sum(y for x, y in drawn) / len(drawn)
        self.assertAlmostEqual(avg_x, 7.5, delta=2.5,
            msg=f"Centroid x={avg_x:.1f} too far from centre — horizontal bias?")
        self.assertAlmostEqual(avg_y, 7.5, delta=2.5,
            msg=f"Centroid y={avg_y:.1f} too far from centre — stem bias?")

    # ── Cycle 8: deterministic — same every play ─────────────────────────────

    def test_identical_on_every_play(self):
        """The flower looks the same on every button press — no random variation."""
        def fingerprint():
            _clock.reset()
            g = _make_graphics()
            flower_module.play(self.su, g)
            return tuple(c.args for c in g.create_pen.call_args_list)

        self.assertEqual(fingerprint(), fingerprint())

    # ── Cycle 9: petals are pink ──────────────────────────────────────────────

    def test_petals_are_pink(self):
        """Petal pixels must be pink — blue channel >= 100 on at least some drawn pixels.

        This distinguishes a pink flower from an orange one without pinning exact RGB.
        Orange has b < 60; pink has b >= 100.
        """
        flower_module.play(self.su, self.graphics)
        pink_pens = [
            (r, g, b)
            for c in self.graphics.create_pen.call_args_list
            for r, g, b in [c.args]
            if (r, g, b) != (0, 0, 0) and b >= 100
        ]
        self.assertGreater(len(pink_pens), 0,
                           "No pink pixels drawn — blue channel never >= 100")

    # ── Cycle 10: pale tips exist ─────────────────────────────────────────────

    def test_pale_tips_drawn(self):
        """Petal tips are lighter than the main petal colour.

        The pale tip (high r+g+b) must appear among drawn pixels.
        We define 'pale' as g >= 150 AND b >= 150 (the cream/pale-pink tip colour).
        """
        flower_module.play(self.su, self.graphics)
        pale_pens = [
            (r, g, b)
            for c in self.graphics.create_pen.call_args_list
            for r, g, b in [c.args]
            if g >= 150 and b >= 150
        ]
        self.assertGreater(len(pale_pens), 0,
                           "No pale tip pixels drawn — missing tip colour")

    # ── Cycle 11: bloom grows outward ────────────────────────────────────────

    def test_bloom_grows_outward(self):
        """Pixels drawn in the early animation reach less far from centre than at the end.

        We track the maximum distance from (7.5, 7.5) of each pixel drawn per frame.
        su.update() marks the end of each frame — we bucket drawn pixels by update call.
        """
        frames     = []
        current    = []

        def on_pixel(_g, x, y):
            current.append((x, y))

        original_update = self.su.update
        def on_update(_g):
            if current:
                frames.append(list(current))
                current.clear()

        self.su.update.side_effect = on_update

        with patch.object(flower_module.display, "pixel", side_effect=on_pixel):
            flower_module.play(self.su, self.graphics)

        # Animation phase: first frame is the bud, last frame before hold is full bloom
        self.assertGreater(len(frames), 4, "Expected multiple animation frames")

        def max_dist(frame):
            return max(((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 for x, y in frame)

        first_max = max_dist(frames[0])
        last_max  = max_dist(frames[-1])
        self.assertLess(first_max, last_max,
                        f"First frame max dist {first_max:.1f} not less than "
                        f"last frame max dist {last_max:.1f} — bloom not growing")


if __name__ == "__main__":
    unittest.main()
