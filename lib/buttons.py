"""
Button GPIO setup and debouncing for the 4 arcade buttons.
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

# Debounce time in milliseconds
DEBOUNCE_MS = 50

# Button objects
_buttons = {}
_last_press_time = {}


def init():
    """Initialize all button GPIO pins with pull-ups."""
    global _buttons, _last_press_time
    for name, pin_num in BUTTON_PINS.items():
        _buttons[name] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        _last_press_time[name] = 0


def is_pressed(name):
    """
    Check if a button is currently pressed (active low).
    Does not handle debouncing - use get_pressed() for that.
    """
    if name not in _buttons:
        return False
    return _buttons[name].value() == 0


def get_pressed():
    """
    Check all buttons and return the name of a pressed button (debounced).
    Returns None if no button is pressed.
    Returns the first pressed button found (priority: heart, star, moon, flower).
    """
    current_time = time.ticks_ms()

    for name in ['heart', 'star', 'moon', 'flower']:
        if name not in _buttons:
            continue
        if _buttons[name].value() == 0:  # Button pressed (active low)
            # Check debounce
            if time.ticks_diff(current_time, _last_press_time[name]) > DEBOUNCE_MS:
                _last_press_time[name] = current_time
                return name
    return None


def any_pressed():
    """Check if any button is currently pressed (no debounce)."""
    for name in _buttons:
        if _buttons[name].value() == 0:
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
