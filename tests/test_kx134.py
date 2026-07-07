"""
Behavioural tests for the KX134 accelerometer driver.
Run from the project root:  python3 -m unittest tests.test_kx134
"""

import sys
import struct
import types
import unittest
from unittest.mock import MagicMock

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
    i2c.readfrom_mem.return_value = b'\x00\x00\x00\x00\x00\x00'
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

def _i2c_returning_xyz(x_raw, y_raw, z_raw):
    """I2C mock that returns all three axes for a 6-byte read at XOUTL."""
    i2c = MagicMock()
    def readfrom_mem(addr, reg, n):
        if reg == KX134._REG_XOUTL:
            return struct.pack("<hhh", x_raw, y_raw, z_raw)[:n]
        return b'\x00' * n
    i2c.readfrom_mem.side_effect = readfrom_mem
    return i2c


# ── Test cases ────────────────────────────────────────────────────────────────

class KX134InitTest(unittest.TestCase):

    def test_init_does_not_raise(self):
        """KX134 can be instantiated with a mock I2C bus without raising."""
        i2c = _make_i2c()
        kx = KX134(i2c)


class KX134ReadXYTest(unittest.TestCase):

    def test_read_xy_returns_two_floats(self):
        """read_xy() returns a tuple of two float values."""
        kx = KX134(_make_i2c())
        result = kx.read_xy()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], float)
        self.assertIsInstance(result[1], float)

    def test_read_xy_positive_gforce_conversion(self):
        """4096 raw counts → 1.0 g for ±8 g range (32768 / 8 = 4096 LSB/g)."""
        kx = KX134(_i2c_returning_xy(x_raw=4096, y_raw=8192))
        x, y = kx.read_xy()
        self.assertAlmostEqual(x, 1.0, places=4)
        self.assertAlmostEqual(y, 2.0, places=4)

    def test_read_xy_negative_gforce_conversion(self):
        """Negative raw values (tilt opposite direction) yield negative G-force."""
        kx = KX134(_i2c_returning_xy(x_raw=-4096, y_raw=-8192))
        x, y = kx.read_xy()
        self.assertAlmostEqual(x, -1.0, places=4)
        self.assertAlmostEqual(y, -2.0, places=4)


class KX134ReadXYZTest(unittest.TestCase):

    def test_read_xyz_returns_three_floats(self):
        """read_xyz() returns a tuple of three float values."""
        kx = KX134(_make_i2c())
        result = kx.read_xyz()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        for component in result:
            self.assertIsInstance(component, float)

    def test_read_xyz_gforce_conversion(self):
        """All three axes convert raw counts to G-force (4096 counts = 1.0 g)."""
        kx = KX134(_i2c_returning_xyz(x_raw=4096, y_raw=-8192, z_raw=12288))
        x, y, z = kx.read_xyz()
        self.assertAlmostEqual(x, 1.0, places=4)
        self.assertAlmostEqual(y, -2.0, places=4)
        self.assertAlmostEqual(z, 3.0, places=4)


if __name__ == "__main__":
    unittest.main()
