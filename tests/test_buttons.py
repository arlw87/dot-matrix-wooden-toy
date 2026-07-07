"""
Behavioural tests for the button module's mode-toggle detector.

The Tilt Game is entered and exited by holding the yellow (star) and red
(heart) Animation Buttons together for 5 seconds. buttons.check_mode_toggle()
is polled from the main loop and fires True exactly once per completed hold.

Runs on desktop CPython with hardware stubs.
Run from the project root:  python3 -m unittest tests.test_buttons
"""

import sys
import types
import unittest
from unittest.mock import patch

# ── Fake, settable clock ──────────────────────────────────────────────────────
# Installed before buttons.py is imported so the module binds our fake time.


class _FakeClock:
    def __init__(self):
        self._ms = 0

    def set(self, ms):
        self._ms = ms

    def advance(self, ms):
        self._ms += ms

    def ticks_ms(self):
        return self._ms

    def ticks_diff(self, a, b):
        return a - b


_clock = _FakeClock()

_fake_time = types.ModuleType("time")
_fake_time.ticks_ms = _clock.ticks_ms
_fake_time.ticks_diff = _clock.ticks_diff
_fake_time.sleep_ms = lambda _ms: None
sys.modules["time"] = _fake_time

# ── MicroPython hardware stub ─────────────────────────────────────────────────
from unittest.mock import MagicMock  # noqa: E402

sys.modules.setdefault("machine", MagicMock())

# ── Import module under test ──────────────────────────────────────────────────
from lib import buttons  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _portb_with(*pressed_names):
    """Build a port B byte with the named buttons held (active-low)."""
    val = 0xFF
    for name in pressed_names:
        val &= ~(1 << buttons.BUTTON_BITS[name])
    return val & 0xFF


class ModeToggleTest(unittest.TestCase):

    def setUp(self):
        _clock.set(0)
        buttons.reset_mode_toggle()

    def _hold(self, *names):
        """Patch the hardware read so the named buttons read as held."""
        return patch.object(buttons, "_read_portb", return_value=_portb_with(*names))

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_yellow_red_held_five_seconds_fires_once(self):
        """Holding star + heart for 5s makes check_mode_toggle() return True."""
        with self._hold("star", "heart"):
            self.assertFalse(buttons.check_mode_toggle())  # t=0, start hold
            _clock.advance(5000)
            self.assertTrue(buttons.check_mode_toggle())   # t=5s, fires

    # ── Cycle 2: only one button of the pair is held ─────────────────────────

    def test_single_button_never_fires(self):
        """Holding only the star button (not heart) never toggles, even past 5s."""
        with self._hold("star"):
            self.assertFalse(buttons.check_mode_toggle())
            _clock.advance(10000)
            self.assertFalse(buttons.check_mode_toggle())

    # ── Cycle 3: fires once, not every poll ──────────────────────────────────

    def test_fires_only_once_while_held(self):
        """Continuing to hold past 5s does not re-fire on every poll."""
        with self._hold("star", "heart"):
            buttons.check_mode_toggle()           # start hold at t=0
            _clock.advance(5000)
            self.assertTrue(buttons.check_mode_toggle())   # fires once
            _clock.advance(1000)
            self.assertFalse(buttons.check_mode_toggle())  # still held, no re-fire
            _clock.advance(5000)
            self.assertFalse(buttons.check_mode_toggle())  # still no re-fire

    # ── Cycle 4: releasing before 5s resets the hold timer ───────────────────

    def test_partial_hold_then_release_resets_timer(self):
        """A hold released before 5s does not count toward the next hold."""
        with self._hold("star", "heart"):
            buttons.check_mode_toggle()           # start hold at t=0
            _clock.advance(3000)
            self.assertFalse(buttons.check_mode_toggle())  # 3s, not yet
        # Buttons released.
        with self._hold():
            self.assertFalse(buttons.check_mode_toggle())
        # Re-hold: needs a fresh 5s, so 3s more is not enough.
        with self._hold("star", "heart"):
            self.assertFalse(buttons.check_mode_toggle())  # restart hold
            _clock.advance(3000)
            self.assertFalse(buttons.check_mode_toggle())  # only 3s into re-hold
            _clock.advance(2000)
            self.assertTrue(buttons.check_mode_toggle())   # now 5s into re-hold

    # ── Cycle 5: same gesture toggles again (enter, then exit) ────────────────

    def test_gesture_can_fire_again_after_release(self):
        """After firing (enter) and releasing, another 5s hold fires again (exit)."""
        with self._hold("star", "heart"):
            buttons.check_mode_toggle()           # start hold
            _clock.advance(5000)
            self.assertTrue(buttons.check_mode_toggle())   # 1st fire (enter game)
        # Release the buttons.
        with self._hold():
            self.assertFalse(buttons.check_mode_toggle())
        # Hold again for a full 5s → fires again to exit.
        with self._hold("star", "heart"):
            self.assertFalse(buttons.check_mode_toggle())
            _clock.advance(5000)
            self.assertTrue(buttons.check_mode_toggle())   # 2nd fire (exit game)


class RocketToggleTest(unittest.TestCase):
    """The Rocket Blast-off game uses the blue (boat) + pink (butterfly) combo."""

    def setUp(self):
        _clock.set(0)
        buttons.reset_mode_toggle()

    def _hold(self, *names):
        return patch.object(buttons, "_read_portb", return_value=_portb_with(*names))

    def test_blue_pink_held_five_seconds_fires_once(self):
        """Holding boat + butterfly for 5s makes check_rocket_toggle() return True."""
        with self._hold("boat", "butterfly"):
            self.assertFalse(buttons.check_rocket_toggle())  # t=0, start hold
            _clock.advance(5000)
            self.assertTrue(buttons.check_rocket_toggle())   # t=5s, fires

    def test_single_button_never_fires(self):
        """Holding only the boat button never toggles the rocket game."""
        with self._hold("boat"):
            self.assertFalse(buttons.check_rocket_toggle())
            _clock.advance(10000)
            self.assertFalse(buttons.check_rocket_toggle())

    def test_rocket_and_tilt_combos_are_independent(self):
        """The star+heart combo does not fire the rocket toggle, and vice versa."""
        # Holding the tilt combo for 5s fires tilt, never rocket.
        with self._hold("star", "heart"):
            buttons.check_mode_toggle()
            buttons.check_rocket_toggle()
            _clock.advance(5000)
            self.assertTrue(buttons.check_mode_toggle())
            self.assertFalse(buttons.check_rocket_toggle())
        buttons.reset_mode_toggle()
        _clock.set(0)
        # Holding the rocket combo for 5s fires rocket, never tilt.
        with self._hold("boat", "butterfly"):
            buttons.check_mode_toggle()
            buttons.check_rocket_toggle()
            _clock.advance(5000)
            self.assertTrue(buttons.check_rocket_toggle())
            self.assertFalse(buttons.check_mode_toggle())


if __name__ == "__main__":
    unittest.main()
