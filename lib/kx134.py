"""
Minimal MicroPython driver for the SparkFun KX134-1211 accelerometer.

Connected via Qwiic (I2C0, GP4/GP5). Shares the bus with the MCP23017 (0x20).
Register map from Kionix KX134-1211 Technical Reference Manual Rev 1.0.

Measures the X/Y/Z axes only. Double-tap/knock detection (both the hardware
Directional-Tap engine and a software jerk detector) was prototyped and removed;
see docs/double-tap-detection.md if you want to revive it.
"""

from machine import I2C

_ADDR_DEFAULT = 0x1F

# Acceleration output (little-endian 16-bit signed pairs)
_REG_XOUTL = 0x08
_REG_YOUTL = 0x0A
_REG_ZOUTL = 0x0C

# Control
_REG_CNTL1  = 0x1B   # PC1=bit7 run, RES=bit6 16-bit, GSEL=bits4:3
_REG_ODCNTL = 0x21   # output data rate (0x09 = 400 Hz)

# CNTL1 bit masks
_PC1     = 0x80   # operating mode (1 = run)
_RES     = 0x40   # resolution (1 = 16-bit)
_GSEL_8G = 0x00   # g-range bits4:3 = 00 → ±8 g
_SCALE_8G = 8.0 / 32768.0


def _to_signed(raw):
    return raw - 0x10000 if raw >= 0x8000 else raw


class KX134:

    _REG_XOUTL = _REG_XOUTL
    _REG_YOUTL = _REG_YOUTL

    def __init__(self, i2c, address=_ADDR_DEFAULT):
        self._i2c   = i2c
        self._addr  = address
        self._scale = _SCALE_8G
        self._init_hardware()

    def _init_hardware(self):
        self._write(_REG_CNTL1, 0x00)                    # standby
        self._write(_REG_ODCNTL, 0x09)                   # 400 Hz output data rate
        self._write(_REG_CNTL1, _PC1 | _RES | _GSEL_8G)  # run mode, 16-bit, ±8 g

    # ── Internal I2C helpers ──────────────────────────────────────────────────

    def _write(self, reg, value):
        self._i2c.writeto_mem(self._addr, reg, bytes([value]))

    def _read(self, reg, n=1):
        return self._i2c.readfrom_mem(self._addr, reg, n)

    # ── Public interface ──────────────────────────────────────────────────────

    def read_xy(self):
        """Return (x, y) acceleration as signed G-force floats."""
        xb = self._read(_REG_XOUTL, 2)
        yb = self._read(_REG_YOUTL, 2)
        x = _to_signed(xb[0] | (xb[1] << 8))
        y = _to_signed(yb[0] | (yb[1] << 8))
        return x * self._scale, y * self._scale

    def read_xyz(self):
        """Return (x, y, z) acceleration as signed G-force floats (one I2C read)."""
        b = self._read(_REG_XOUTL, 6)
        x = _to_signed(b[0] | (b[1] << 8))
        y = _to_signed(b[2] | (b[3] << 8))
        z = _to_signed(b[4] | (b[5] << 8))
        return x * self._scale, y * self._scale, z * self._scale
