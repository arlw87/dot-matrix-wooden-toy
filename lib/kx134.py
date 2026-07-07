"""
Minimal MicroPython driver for the SparkFun KX134-1211 accelerometer.

Connected via Qwiic (I2C0, GP4/GP5). Shares the bus with the MCP23017 (0x20).
Register map sourced from the Kionix KX134-1211 Technical Reference Manual.
"""

from machine import I2C

_ADDR_DEFAULT = 0x1F

# Acceleration output (little-endian 16-bit signed pairs)
_REG_XOUTL = 0x08
_REG_YOUTL = 0x0A

# Control
_REG_CNTL1  = 0x1B   # PC1=bit7 run, RES=bit6 16-bit, GSEL=bits4:3, TDTE=bit2 tap
_REG_ODCNTL = 0x21   # output data rate

# Interrupt
_REG_INS2    = 0x17  # bits[3:2]: TDTS — 00=none, 01=single, 10=double
_REG_INT_REL = 0x1A  # write any byte to release latched interrupt

# Tap/double-tap detection
_REG_TDTRC = 0x24    # bit0=STRE single, bit1=DTRE double
_REG_TDTC  = 0x25    # debounce counter
_REG_TTH   = 0x26    # tap threshold
_REG_FTD   = 0x28    # first tap detect window
_REG_STD   = 0x29    # second tap detect window
_REG_TLT   = 0x2A    # tap latency timer
_REG_TWS   = 0x2B    # tap window

# CNTL1 bit masks
_PC1  = 0x80   # operating mode
_RES  = 0x40   # 16-bit resolution
_TDTE = 0x04   # tap/double-tap engine enable
# GSEL 00 → ±8 g (bits 4:3 = 0b00)
_GSEL_8G = 0x00
_SCALE_8G = 8.0 / 32768.0

# TDTS field in INS2
_TDTS_DOUBLE = 0x08   # bits[3:2] = 0b10 → double tap


class KX134:

    _REG_XOUTL   = _REG_XOUTL
    _REG_YOUTL   = _REG_YOUTL
    _REG_INS2    = _REG_INS2
    _REG_INT_REL = _REG_INT_REL

    def __init__(self, i2c, address=_ADDR_DEFAULT):
        self._i2c  = i2c
        self._addr = address
        self._scale = _SCALE_8G
        self._init_hardware()

    def _init_hardware(self):
        # Standby mode before configuring
        self._write(_REG_CNTL1, 0x00)
        # 50 Hz output data rate (OSA = 0x06)
        self._write(_REG_ODCNTL, 0x06)
        # Enable double-tap report only
        self._write(_REG_TDTRC, 0x02)
        # Run mode: 16-bit, ±8 g, tap engine on
        self._write(_REG_CNTL1, _PC1 | _RES | _GSEL_8G | _TDTE)

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
        x_raw = xb[0] | (xb[1] << 8)
        y_raw = yb[0] | (yb[1] << 8)
        if x_raw >= 0x8000:
            x_raw -= 0x10000
        if y_raw >= 0x8000:
            y_raw -= 0x10000
        return x_raw * self._scale, y_raw * self._scale

    def configure_double_tap(self, threshold=0x40, window=0x28):
        """Configure the hardware double-tap interrupt threshold and window."""
        self._write(_REG_CNTL1, 0x00)        # standby
        self._write(_REG_TTH, threshold)
        self._write(_REG_TWS, window)
        self._write(_REG_CNTL1, _PC1 | _RES | _GSEL_8G | _TDTE)

    def poll_double_tap(self):
        """Return True once if a hardware double-tap has fired; clears the latch."""
        ins2 = self._read(_REG_INS2)[0]
        fired = (ins2 & 0x0C) == _TDTS_DOUBLE
        if fired:
            self._write(_REG_INT_REL, 0x00)
        return fired
