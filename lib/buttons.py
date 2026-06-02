"""
Button input for the 4 arcade buttons.
- heart: Adafruit MCP23017 GPB0 via I2C (STEMMA QT)
- star, moon, flower: direct GPIO pins (active-low, internal pull-ups)
Also supports Stellar Unicorn onboard buttons (A, B, C, D) for testing.
"""

from machine import Pin, I2C
import time

# GPIO pin assignments for star, moon, flower
BUTTON_PINS = {
    'star': 1,    # GP1
    'moon': 2,    # GP2
    'flower': 3,  # GP3
}

# MCP23017 I2C config (heart button on GPB0)
MCP23017_ADDR = 0x20   # default address: A0/A1/A2 all wired to GND
MCP23017_SDA  = 4      # GP4 — blue STEMMA QT wire
MCP23017_SCL  = 5      # GP5 — yellow STEMMA QT wire
_REG_IODIRB   = 0x01   # port B direction register (1 = input)
_REG_GPPUB    = 0x0D   # port B pull-up register
_REG_GPIOB    = 0x13   # port B GPIO read register

# Debounce time in milliseconds
DEBOUNCE_MS = 50

# Internal state
_buttons = {}
_last_press_time = {'heart': 0, 'star': 0, 'moon': 0, 'flower': 0}
_stellar_unicorn = None
_i2c = None


def init(su=None):
    """Initialize GPIO buttons and MCP23017 over I2C."""
    global _buttons, _last_press_time, _stellar_unicorn, _i2c
    _stellar_unicorn = su

    for name, pin_num in BUTTON_PINS.items():
        _buttons[name] = Pin(pin_num, Pin.IN, Pin.PULL_UP)

    # Init MCP23017 for heart button (GPB0)
    _i2c = I2C(0, sda=Pin(MCP23017_SDA), scl=Pin(MCP23017_SCL), freq=400000)
    _i2c.writeto_mem(MCP23017_ADDR, _REG_IODIRB, b'\xff')  # all port B pins as inputs
    _i2c.writeto_mem(MCP23017_ADDR, _REG_GPPUB,  b'\xff')  # enable pull-ups on port B


def _read_mcp_gpb0():
    """Read MCP23017 GPB0. Active-low: returns True when button is pressed."""
    if _i2c is None:
        return False
    val = _i2c.readfrom_mem(MCP23017_ADDR, _REG_GPIOB, 1)[0]
    return (val & 0x01) == 0  # GPB0 is bit 0; low = pressed


def _check_onboard_button(name):
    """Check if the corresponding onboard Stellar Unicorn button is pressed."""
    if _stellar_unicorn is None:
        return False
    from stellar import StellarUnicorn
    button_map = {
        'heart': StellarUnicorn.SWITCH_A,
        'star':  StellarUnicorn.SWITCH_B,
        'moon':  StellarUnicorn.SWITCH_C,
        'flower': StellarUnicorn.SWITCH_D,
    }
    if name in button_map:
        return _stellar_unicorn.is_pressed(button_map[name])
    return False


def is_pressed(name):
    """Check if a button is currently pressed (no debounce)."""
    if name == 'heart':
        return _read_mcp_gpb0() or _check_onboard_button('heart')
    if name in _buttons and _buttons[name].value() == 0:
        return True
    return _check_onboard_button(name)


def get_pressed():
    """
    Return the name of a debounced button press, or None.
    Priority: heart, star, moon, flower.
    """
    current_time = time.ticks_ms()

    # Debug: log raw state
    pressed_buttons = []
    for name in ['heart', 'star', 'moon', 'flower']:
        mcp_pressed    = (name == 'heart') and _read_mcp_gpb0()
        gpio_pressed   = name in _buttons and _buttons[name].value() == 0
        onboard_pressed = _check_onboard_button(name)
        if mcp_pressed or gpio_pressed or onboard_pressed:
            src = ('M' if mcp_pressed else '') + ('G' if gpio_pressed else '') + ('O' if onboard_pressed else '')
            pressed_buttons.append(f"{name}({src})")

    if pressed_buttons:
        print(f"[BTN DEBUG] Raw pressed: {', '.join(pressed_buttons)}")

    for name in ['heart', 'star', 'moon', 'flower']:
        mcp_pressed     = (name == 'heart') and _read_mcp_gpb0()
        gpio_pressed    = name in _buttons and _buttons[name].value() == 0
        onboard_pressed = _check_onboard_button(name)

        if mcp_pressed or gpio_pressed or onboard_pressed:
            if time.ticks_diff(current_time, _last_press_time[name]) > DEBOUNCE_MS:
                _last_press_time[name] = current_time
                print(f"[BTN DEBUG] Returning: {name}")
                return name
    return None


def any_pressed():
    """Check if any button is currently pressed (no debounce)."""
    if _read_mcp_gpb0():
        return True
    for name in _buttons:
        if _buttons[name].value() == 0:
            return True
    for name in ['heart', 'star', 'moon', 'flower']:
        if _check_onboard_button(name):
            return True
    return False


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
