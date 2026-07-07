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

# Tap/double-tap detection (addresses from KX134-1211 datasheet §6)
_REG_TDTRC = 0x29    # bit0=STRE single, bit1=DTRE double
_REG_TDTC  = 0x2A    # debounce counter
_REG_TTH   = 0x2B    # tap threshold high
_REG_TTL   = 0x2C    # tap threshold low
_REG_FTD   = 0x2D    # first tap detect window
_REG_STD   = 0x2E    # second tap detect window
_REG_TLT   = 0x2F    # tap latency timer
_REG_TWS   = 0x30    # tap window

# CNTL1 bit masks
_PC1  = 0x80   # operating mode
_RES  = 0x40   # 16-bit resolution
_TDTE = 0x04   # tap/double-tap engine enable
# GSEL 00 → ±8 g (bits 4:3 = 0b00)
_GSEL_8G = 0x00
_SCALE_8G = 8.0 / 32768.0

# TDTS field in INS2 bits[1:0]: 00=none, 01=single, 10=double
_TDTS_MASK   = 0x03
_TDTS_DOUBLE = 0x02


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
        self._write(_REG_CNTL1, 0x00)                           # standby
        self._write(_REG_ODCNTL, 0x09)                          # 400 Hz ODR — required for tap timing
        self._write(_REG_TDTRC, 0x02)                           # enable double-tap report
        self._write(_REG_CNTL1, _PC1 | _RES | _GSEL_8G | _TDTE)  # run mode
        self._read(_REG_INT_REL)                                 # clear boot-time latch

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

    def configure_double_tap(self, threshold=0x01, window=0xFF):
        """Configure the hardware double-tap interrupt threshold and window.

        Timing values are tuned for 400 Hz ODR (1 sample = 2.5 ms).
        threshold: tap detection threshold — 0x01 is most sensitive.
        window: max samples for the full double-tap gesture (0xFF = ~637 ms).
        """
        self._write(_REG_CNTL1, 0x00)      # standby before changing tap registers
        self._write(_REG_TDTC, 0x00)       # no debounce — fire on any impulse
        self._write(_REG_TTH,  threshold)  # tap threshold high
        self._write(_REG_TTL,  threshold)  # tap threshold low (match high for max sensitivity)
        self._write(_REG_FTD,  0xA2)       # PTAP=5 (12.5 ms), FTDV=2 — standard first-tap timing
        self._write(_REG_STD,  0x24)       # standard second-tap timing
        self._write(_REG_TLT,  0x10)       # latency: 16 samples (40 ms) before 2nd tap window
        self._write(_REG_TWS,  window)     # tap window: max time for complete double-tap
        self._write(_REG_CNTL1, _PC1 | _RES | _GSEL_8G | _TDTE)
        self._read(_REG_INT_REL)           # clear any latch held during reconfigure

    def poll_double_tap(self):
        """Return True once if a hardware double-tap has fired; clears the latch."""
        ins2 = self._read(_REG_INS2)[0]
        fired = (ins2 & _TDTS_MASK) == _TDTS_DOUBLE
        if fired:
            self._write(_REG_INT_REL, 0x00)
        return fired

    def dump_interrupt_regs(self):
        """Print raw interrupt register bytes — for diagnosing tap detection."""
        ins1 = self._read(0x16)[0]
        ins2 = self._read(0x17)[0]
        ins3 = self._read(0x18)[0]
        print(f"[KX134] INS1=0x{ins1:02X} INS2=0x{ins2:02X} INS3=0x{ins3:02X}  "
              f"INS2 bits={ins2:08b}")
