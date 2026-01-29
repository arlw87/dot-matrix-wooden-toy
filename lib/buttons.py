"""
Button GPIO setup and debouncing for the 4 arcade buttons.
Also supports Stellar Unicorn onboard buttons (A, B, C, D) for testing.
Buttons are active-low (pressed = LOW) with internal pull-ups.
"""

from machine import Pin
import time

# GPIO pin assignments for the 4 arcade buttons
# Adjust these based on your wiring
BUTTON_PINS = {
    'heart': 0,   # GP0
    'star': 1,    # GP1
    'moon': 2,    # GP2
    'flower': 3,  # GP3
}

# Stellar Unicorn onboard button mapping (for testing without external buttons)
# These are checked via su.is_pressed() not GPIO
ONBOARD_BUTTON_MAP = {
    'heart': 'SWITCH_A',
    'star': 'SWITCH_B',
    'moon': 'SWITCH_C',
    'flower': 'SWITCH_D',
}

# Debounce time in milliseconds
DEBOUNCE_MS = 50

# Button objects
_buttons = {}
_last_press_time = {}
_stellar_unicorn = None  # Reference to StellarUnicorn for onboard buttons


def init(su=None):
    """
    Initialize all button GPIO pins with pull-ups.

    Args:
        su: Optional StellarUnicorn instance to enable onboard button testing
    """
    global _buttons, _last_press_time, _stellar_unicorn
    _stellar_unicorn = su

    for name, pin_num in BUTTON_PINS.items():
        _buttons[name] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        _last_press_time[name] = 0


def _check_onboard_button(name):
    """Check if onboard Stellar Unicorn button is pressed."""
    if _stellar_unicorn is None:
        return False

    from stellar import StellarUnicorn
    button_map = {
        'heart': StellarUnicorn.SWITCH_A,
        'star': StellarUnicorn.SWITCH_B,
        'moon': StellarUnicorn.SWITCH_C,
        'flower': StellarUnicorn.SWITCH_D,
    }

    if name in button_map:
        return _stellar_unicorn.is_pressed(button_map[name])
    return False


def is_pressed(name):
    """
    Check if a button is currently pressed (GPIO or onboard).
    Does not handle debouncing - use get_pressed() for that.
    """
    # Check GPIO button
    if name in _buttons and _buttons[name].value() == 0:
        return True
    # Check onboard button
    return _check_onboard_button(name)


def get_pressed():
    """
    Check all buttons and return the name of a pressed button (debounced).
    Returns None if no button is pressed.
    Returns the first pressed button found (priority: heart, star, moon, flower).
    Checks both GPIO pins and Stellar Unicorn onboard buttons.
    """
    current_time = time.ticks_ms()

    # Debug: check raw state of all buttons
    pressed_buttons = []
    for name in ['heart', 'star', 'moon', 'flower']:
        gpio_pressed = name in _buttons and _buttons[name].value() == 0
        onboard_pressed = _check_onboard_button(name)
        if gpio_pressed or onboard_pressed:
            pressed_buttons.append(f"{name}({'G' if gpio_pressed else ''}{'O' if onboard_pressed else ''})")

    if pressed_buttons:
        print(f"[BTN DEBUG] Raw pressed: {', '.join(pressed_buttons)}")

    for name in ['heart', 'star', 'moon', 'flower']:
        # Check GPIO button
        gpio_pressed = name in _buttons and _buttons[name].value() == 0
        # Check onboard button
        onboard_pressed = _check_onboard_button(name)

        if gpio_pressed or onboard_pressed:
            # Check debounce
            if time.ticks_diff(current_time, _last_press_time[name]) > DEBOUNCE_MS:
                _last_press_time[name] = current_time
                print(f"[BTN DEBUG] Returning: {name}")
                return name
    return None


def any_pressed():
    """Check if any button is currently pressed (no debounce)."""
    for name in _buttons:
        if _buttons[name].value() == 0:
            return True
    # Also check onboard buttons
    for name in ['heart', 'star', 'moon', 'flower']:
        if _check_onboard_button(name):
            return True
    return False


def wait_for_release():
    """Wait until all buttons are released."""
    while any_pressed():
        time.sleep_ms(10)


def wait_for_press():
    """
    Block until a button is pressed, then return its name.
    Includes debouncing.
    """
    # First wait for all buttons to be released
    wait_for_release()
    # Then wait for a press
    while True:
        pressed = get_pressed()
        if pressed:
            return pressed
        time.sleep_ms(10)
