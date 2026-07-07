"""
Behavioural tests for the KX134 accelerometer driver.
Run from the project root:  python3 -m unittest tests.test_kx134
"""

import sys
import struct
import types
import unittest
from unittest.mock import MagicMock, call

# ── MicroPython hardware stub ─────────────────────────────────────────────────
sys.modules.setdefault("machine", MagicMock())

# ── Fake time module ──────────────────────────────────────────────────────────
class _FakeClock:
    def __init__(self):
        self._ms = 0

    def set(self, ms):
        self._ms = ms

    def ticks_ms(self):
        return self._ms

    def ticks_diff(self, a, b):
        return a - b


_clock = _FakeClock()
_fake_time = types.ModuleType("time")
_fake_time.ticks_ms   = _clock.ticks_ms
_fake_time.ticks_diff = _clock.ticks_diff
sys.modules["time"] = _fake_time

# ── Import module under test ──────────────────────────────────────────────────
from lib.kx134 import KX134  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_i2c():
    i2c = MagicMock()
    i2c.readfrom_mem.return_value = b'\x00\x00'
    return i2c

def _raw_bytes(value_int16):
    """Pack a signed 16-bit int into two little-endian bytes."""
    return struct.pack("<h", value_int16)

def _i2c_returning_xy(x_raw, y_raw):
    """I2C mock that returns x_raw for X reads and y_raw for Y reads."""
    i2c = MagicMock()
    def readfrom_mem(addr, reg, n):
        if reg == KX134._REG_XOUTL:
            return _raw_bytes(x_raw)
        if reg == KX134._REG_YOUTL:
            return _raw_bytes(y_raw)
        return b'\x00' * n
    i2c.readfrom_mem.side_effect = readfrom_mem
    return i2c


# ── Test cases ────────────────────────────────────────────────────────────────

class KX134InitTest(unittest.TestCase):

    # ── Cycle 1: tracer bullet ────────────────────────────────────────────────

    def test_init_does_not_raise(self):
        """KX134 can be instantiated with a mock I2C bus without raising."""
        i2c = _make_i2c()
        kx = KX134(i2c)


class KX134ReadXYTest(unittest.TestCase):

    # ── Cycle 2: read_xy() returns two floats ────────────────────────────────

    def test_read_xy_returns_two_floats(self):
        """read_xy() returns a tuple of two float values."""
        kx = KX134(_make_i2c())
        result = kx.read_xy()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], float)

    # ── Cycle 3: positive G-force conversion ─────────────────────────────────

    def test_read_xy_positive_gforce_conversion(self):
        """4096 raw counts → 1.0 g for ±8 g range (32768 / 8 = 4096 LSB/g)."""
        kx = KX134(_i2c_returning_xy(x_raw=4096, y_raw=8192))
        x, y = kx.read_xy()
        self.assertAlmostEqual(x, 1.0, places=4)
        self.assertAlmostEqual(y, 2.0, places=4)

    # ── Cycle 4: negative G-force (2's complement) ───────────────────────────

    def test_read_xy_negative_gforce_conversion(self):
        """Negative raw values (tilt opposite direction) yield negative G-force."""
        kx = KX134(_i2c_returning_xy(x_raw=-4096, y_raw=-8192))
        x, y = kx.read_xy()
        self.assertAlmostEqual(x, -1.0, places=4)
        self.assertAlmostEqual(y, -2.0, places=4)


class KX134DoubleTapTest(unittest.TestCase):

    def _make_kx(self, ins2_value=0x00):
        """KX134 whose INS2 register always returns ins2_value."""
        i2c = MagicMock()
        def readfrom_mem(addr, reg, n):
            if reg == KX134._REG_INS2:
                return bytes([ins2_value])
            return b'\x00' * n
        i2c.readfrom_mem.side_effect = readfrom_mem
        return KX134(i2c), i2c

    # ── Cycle 5: no interrupt ─────────────────────────────────────────────────

    def test_poll_double_tap_false_when_quiet(self):
        """poll_double_tap() returns False when no tap interrupt is set."""
        kx, _ = self._make_kx(ins2_value=0x00)
        self.assertFalse(kx.poll_double_tap())

    # ── Cycle 6: double-tap interrupt fires ───────────────────────────────────

    def test_poll_double_tap_true_when_double_tap_bit_set(self):
        """poll_double_tap() returns True when INS2 reports a double-tap (bits[1:0]=0b10)."""
        kx, _ = self._make_kx(ins2_value=0x02)   # 0b00000010
        self.assertTrue(kx.poll_double_tap())

    # ── Cycle 7: latch clears ─────────────────────────────────────────────────

    def test_poll_double_tap_clears_latch(self):
        """After detecting a double-tap, poll_double_tap() writes INT_REL to clear the latch."""
        kx, i2c = self._make_kx(ins2_value=0x02)
        kx.poll_double_tap()
        write_calls = [c for c in i2c.writeto_mem.call_args_list
                       if c.args[1] == KX134._REG_INT_REL]
        self.assertEqual(len(write_calls), 1,
            msg="Expected exactly one write to INT_REL to clear the latch")

    def test_poll_double_tap_no_latch_clear_when_quiet(self):
        """poll_double_tap() does NOT write INT_REL when no interrupt is set."""
        kx, i2c = self._make_kx(ins2_value=0x00)
        kx.poll_double_tap()
        write_calls = [c for c in i2c.writeto_mem.call_args_list
                       if c.args[1] == KX134._REG_INT_REL]
        self.assertEqual(len(write_calls), 0,
            msg="INT_REL should not be written when there is no interrupt")


if __name__ == "__main__":
    unittest.main()
