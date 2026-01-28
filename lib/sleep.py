"""
Auto-sleep timer and sleep/wake logic.
The toy sleeps after 2 minutes of inactivity to conserve battery.
"""

import time
import machine

# Sleep timeout in milliseconds (2 minutes)
SLEEP_TIMEOUT_MS = 2 * 60 * 1000

# Last activity timestamp
_last_activity = 0


def reset_timer():
    """Reset the inactivity timer (call on any button press)."""
    global _last_activity
    _last_activity = time.ticks_ms()


def should_sleep():
    """Check if the inactivity timeout has been reached."""
    if _last_activity == 0:
        return False
    elapsed = time.ticks_diff(time.ticks_ms(), _last_activity)
    return elapsed >= SLEEP_TIMEOUT_MS


def time_until_sleep_ms():
    """Return milliseconds until sleep, or 0 if should sleep now."""
    if _last_activity == 0:
        return SLEEP_TIMEOUT_MS
    elapsed = time.ticks_diff(time.ticks_ms(), _last_activity)
    remaining = SLEEP_TIMEOUT_MS - elapsed
    return max(0, remaining)


def enter_sleep(su, graphics):
    """
    Enter low-power sleep mode.
    Display is turned off, minimal power consumption.
    Any button press will wake the device.
    """
    from lib import display, buttons

    # Ensure display is off
    display.clear(graphics, su)

    # Enter light sleep - wake on any GPIO change
    # The Pico will wake on button press
    # For now we use a polling sleep since dormant mode requires specific setup
    while True:
        # Check for button press to wake
        if buttons.any_pressed():
            reset_timer()
            buttons.wait_for_release()
            return  # Wake up

        # Light sleep for a short period
        time.sleep_ms(100)


def init():
    """Initialize the sleep timer."""
    reset_timer()
