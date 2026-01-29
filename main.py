"""
Dot Matrix Wooden Toy - Main Program
=====================================
An interactive toy for toddlers featuring a 16x16 RGB LED matrix.
Press one of four buttons (Heart, Star, Moon, Flower) to trigger
colorful animations with sound effects.

Hardware: Pimoroni Stellar Unicorn with Raspberry Pi Pico 2 W
"""

import gc
gc.collect()  # Clean memory before any allocations

# CRITICAL: Import sound FIRST to allocate audio buffer before fragmentation
from lib import sound

import time
from stellar import StellarUnicorn
from picographics import PicoGraphics, DISPLAY_STELLAR_UNICORN

# Import remaining modules
from lib import display, buttons, sleep
from animations import get_animation, play_boot

# Configuration
DEFAULT_BRIGHTNESS = 0.5  # 50% brightness
MIN_BRIGHTNESS = 0.1      # Minimum brightness floor
MAX_BRIGHTNESS = 1.0
VOLUME = 0.45             # Fixed moderate volume (~45%)


def setup():
    """Initialize hardware and return instances."""
    # Create Stellar Unicorn and graphics instances
    su = StellarUnicorn()
    graphics = PicoGraphics(display=DISPLAY_STELLAR_UNICORN)

    # Set default brightness and volume
    su.set_brightness(DEFAULT_BRIGHTNESS)
    sound.set_volume(su, VOLUME)

    # Initialize buttons (pass su to enable onboard button testing)
    buttons.init(su)

    # Initialize sleep timer
    sleep.init()

    return su, graphics


def check_brightness_buttons(su):
    """
    Check and handle the Stellar Unicorn's built-in brightness buttons.
    Returns True if a brightness button was pressed.
    """
    brightness_changed = False
    current = su.get_brightness()

    # Check brightness up (Stellar Unicorn button A)
    if su.is_pressed(StellarUnicorn.SWITCH_BRIGHTNESS_UP):
        new_brightness = min(MAX_BRIGHTNESS, current + 0.1)
        su.set_brightness(new_brightness)
        brightness_changed = True

    # Check brightness down (Stellar Unicorn button B)
    if su.is_pressed(StellarUnicorn.SWITCH_BRIGHTNESS_DOWN):
        new_brightness = max(MIN_BRIGHTNESS, current - 0.1)
        su.set_brightness(new_brightness)
        brightness_changed = True

    return brightness_changed


def create_interrupt_checker(su):
    """
    Create a closure that checks for button interrupts.
    Returns a function that returns the name of pressed button or None.
    """
    def check_interrupt():
        # Also handle brightness buttons
        check_brightness_buttons(su)
        # Check for butterfly button first, then individual buttons
        return buttons.get_butterfly_pressed() or buttons.get_pressed()

    return check_interrupt


def main():
    """Main program loop."""
    # Setup hardware
    su, graphics = setup()

    # Play boot animation
    print("Playing boot animation...")
    play_boot(su, graphics)

    # Clear display and go to idle
    display.clear(graphics, su)
    print("Ready - waiting for button press...")

    # Track next button to play (for immediate interrupt handling)
    next_button = None

    while True:
        # Check for auto-sleep
        if sleep.should_sleep():
            print("Entering sleep mode...")
            sleep.enter_sleep(su, graphics)
            print("Woke from sleep")
            # After wake, just go back to idle (no boot animation per PRD)
            next_button = None
            continue

        # Handle brightness buttons
        check_brightness_buttons(su)

        # Check for button press (use queued button or poll for new one)
        # Check butterfly button first, then individual buttons
        pressed = next_button or buttons.get_butterfly_pressed() or buttons.get_pressed()
        next_button = None  # Clear queued button

        if pressed:
            print(f"Button pressed: {pressed}")
            sleep.reset_timer()

            # Get the animation for this button
            animation = get_animation(pressed)

            if animation:
                # Stop any playing sound
                sound.stop(su)

                # Create interrupt checker
                check_interrupt = create_interrupt_checker(su)

                # Play the animation - returns None if completed, or button name if interrupted
                interrupted_by = animation.play(su, graphics, check_interrupt)

                if interrupted_by:
                    print(f"Animation {pressed} interrupted by {interrupted_by}")
                    # Queue the interrupting button for immediate playback
                    next_button = interrupted_by
                else:
                    print(f"Animation {pressed} completed")
                    # Clear display after animation completes normally
                    display.clear(graphics, su)

                # Reset sleep timer after animation ends
                sleep.reset_timer()

        # Small delay to prevent busy-waiting
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
