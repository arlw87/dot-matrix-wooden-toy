"""
BMA400 triple-axis accelerometer driver for MicroPython.
Communicates over I2C bus 0 (SDA=GP4, SCL=GP5 — shared Qwiic/STEMMA QT bus).
Default I2C address: 0x14 (SparkFun breakout, SDO=GND).

Provides:
  - init()               — configure chip, enable double-tap detection
  - read_xyz()           — (x, y, z) tilt in units of g
  - double_tap_detected() — True if a double-tap fired since last call
"""

from machine import Pin, I2C
import time

ADDR = 0x14  # SDO tied to GND on SparkFun board

# ── Register map ──────────────────────────────────────────────────────────────
_REG_CHIP_ID     = 0x00  # Read: 0x90
_REG_ACC_X_LSB   = 0x04  # 6 bytes: X_LSB X_MSB Y_LSB Y_MSB Z_LSB Z_MSB
_REG_INT_STAT1   = 0x0F  # bit 2 = d_tap_int (clears on read)
_REG_ACC_CONF0   = 0x19  # bits[1:0]: power mode  0=sleep 1=low-power 2=normal
_REG_ACC_CONF1   = 0x1A  # bits[7:6]: range  bits[3:0]: ODR
_REG_INT_CONF1   = 0x20  # bit[4]=d_tap_int_en  bit[3]=s_tap_int_en
_REG_TAP_CONFIG  = 0x57  # bits[5:3]: sensitivity (0=max 7=min)  bits[1:0]: axis
_REG_TAP_CONFIG1 = 0x58  # bits[5:4]: quiet_dt  bits[3:2]: quiet  bits[1:0]: tics_th

_i2c = None


def init():
    """Configure BMA400 in normal mode with double-tap detection on the Z-axis."""
    global _i2c
    _i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)

    chip_id = _read(_REG_CHIP_ID)
    if chip_id != 0x90:
        raise RuntimeError("BMA400 not found (got chip_id=0x{:02x})".format(chip_id))

    # Normal power mode, ±2g range (bits[7:6]=00), 100 Hz ODR (0x08)
    _write(_REG_ACC_CONF0, 0x02)
    _write(_REG_ACC_CONF1, 0x08)

    # Tap: Z-axis (0x00), medium sensitivity (4) → bits[5:3]=4, bits[1:0]=0
    _write(_REG_TAP_CONFIG, (4 << 3) | 0x00)
    # Timing: quiet_dt=2, quiet=2, tics_th=3  (reasonable defaults for a toddler tap)
    _write(_REG_TAP_CONFIG1, (2 << 4) | (2 << 2) | 3)

    # Enable double-tap interrupt (bit 4 of INT_CONF1)
    _write(_REG_INT_CONF1, 1 << 4)

    time.sleep_ms(20)  # allow settings to stabilise


def read_xyz():
    """
    Return (x, y, z) acceleration as floats in units of g.

    When flat and still: x≈0, y≈0, z≈±1.
    Tilting the right edge down: x goes positive.
    Tilting the far edge down:   y goes positive.

    Flip signs in the caller if your mounting differs.
    """
    data = _i2c.readfrom_mem(ADDR, _REG_ACC_X_LSB, 6)

    def _signed12(lsb, msb):
        raw = (msb << 4) | (lsb >> 4)
        return raw - 4096 if raw >= 2048 else raw

    # ±2g range → 2048 LSB per g
    s = 1.0 / 2048.0
    return (
        _signed12(data[0], data[1]) * s,
        _signed12(data[2], data[3]) * s,
        _signed12(data[4], data[5]) * s,
    )


def double_tap_detected():
    """Return True if a double-tap has fired since the last call. Status clears on read."""
    return bool(_read(_REG_INT_STAT1) & 0x04)  # bit 2 = d_tap_int


def _read(reg):
    return _i2c.readfrom_mem(ADDR, reg, 1)[0]


def _write(reg, val):
    _i2c.writeto_mem(ADDR, reg, bytes([val]))
