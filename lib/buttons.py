"""
Button input for 6 push-to-make buttons wired to MCP23017 port B.

Pin mapping (active-low, internal pull-ups enabled):
  GPB0 → rocket     (green button)
  GPB1 → boot       (blue button)
  GPB2 → heart      (red button)
  GPB3 → butterfly  (pink button)
  GPB4 → (unassigned — black button)
  GPB5 → star       (yellow button)
"""

from machine import Pin, I2C
import time

# MCP23017 I2C config
MCP23017_ADDR = 0x20   # A0/A1/A2 all wired to GND
MCP23017_SDA  = 4      # GP4 — blue STEMMA QT wire
MCP23017_SCL  = 5      # GP5 — yellow STEMMA QT wire
_REG_IODIRB   = 0x01   # port B direction register (1 = input)
_REG_GPPUB    = 0x0D   # port B pull-up register
_REG_GPIOB    = 0x13   # port B GPIO read register

# Button name → port B bit number
BUTTON_BITS = {
    'rocket':    0,
    'boot':      1,
    'heart':     2,
    'butterfly': 3,
    'star':      5,
}

# Priority order for simultaneous presses
BUTTON_ORDER = ['heart', 'star', 'rocket', 'butterfly', 'boot']

DEBOUNCE_MS = 50

_i2c = None
_last_press_time = {name: 0 for name in BUTTON_BITS}


def init(su=None):
    """Initialize MCP23017 over I2C. su is accepted but unused (kept for compatibility)."""
    global _i2c
    _i2c = I2C(0, sda=Pin(MCP23017_SDA), scl=Pin(MCP23017_SCL), freq=400000)
    _i2c.writeto_mem(MCP23017_ADDR, _REG_IODIRB, b'\xff')  # all port B pins as inputs
    _i2c.writeto_mem(MCP23017_ADDR, _REG_GPPUB,  b'\xff')  # enable pull-ups on port B


def _read_portb():
    """Read port B byte from MCP23017. Returns 0xFF if not initialised."""
    if _i2c is None:
        return 0xFF
    return _i2c.readfrom_mem(MCP23017_ADDR, _REG_GPIOB, 1)[0]


def is_pressed(name):
    """Check if a named button is currently pressed (no debounce)."""
    bit = BUTTON_BITS.get(name)
    if bit is None:
        return False
    return (_read_portb() & (1 << bit)) == 0  # active-low


def get_pressed():
    """
    Return the name of a debounced button press, or None.
    Reads port B once and checks each button in priority order.
    """
    val = _read_portb()
    current_time = time.ticks_ms()

    # Debug: log any raw presses
    pressed_names = [n for n in BUTTON_ORDER if (val & (1 << BUTTON_BITS[n])) == 0]
    if pressed_names:
        print(f"[BTN DEBUG] Raw pressed: {', '.join(pressed_names)}")

    for name in BUTTON_ORDER:
        if (val & (1 << BUTTON_BITS[name])) == 0:  # active-low
            if time.ticks_diff(current_time, _last_press_time[name]) > DEBOUNCE_MS:
                _last_press_time[name] = current_time
                print(f"[BTN DEBUG] Returning: {name}")
                return name

    return None


def any_pressed():
    """Check if any button is currently pressed (no debounce)."""
    val = _read_portb()
    return any((val & (1 << bit)) == 0 for bit in BUTTON_BITS.values())


def wait_for_release():
    """Wait until all buttons are released."""
    while any_pressed():
        time.sleep_ms(10)


def wait_for_press():
    """Block until a button is pressed, then return its name. Includes debouncing."""
    wait_for_release()
    while True:
        pressed = get_pressed()
        if pressed:
            return pressed
        time.sleep_ms(10)
