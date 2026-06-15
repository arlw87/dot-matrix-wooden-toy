"""
Dot Matrix Wooden Toy - Main Program
=====================================
An interactive toy for toddlers featuring a 16x16 RGB LED matrix.

Button mode (default):
  Six push-to-make buttons (MCP23017 GPB0-GPB5) each trigger an animation:
  heart, star, moon, flower, butterfly, boot.

Ball mode:
  Double-tap the toy to enter. Tilt to roll a glowing ball around the screen.
  Double-tap again (or press any button) to return to button mode.

Hardware: Pimoroni Stellar Unicorn + Raspberry Pi Pico 2 W + MCP23017 + BMA400
"""

import gc
gc.collect()  # Clean memory before any allocations

# CRITICAL: Import sound FIRST to allocate audio buffer before fragmentation
from lib import sound

import time
from stellar import StellarUnicorn
from picographics import PicoGraphics, DISPLAY_STELLAR_UNICORN

# Import remaining modules
from lib import display, buttons, sleep, bma400
from animations import get_animation, play_boot

# Configuration
DEFAULT_BRIGHTNESS = 1  # 75% brightness
MIN_BRIGHTNESS = 0.1      # Minimum brightness floor
MAX_BRIGHTNESS = 1.0
VOLUME = 0.45             # Fixed moderate volume (~45%)


def setup():
    """Initialize hardware and return instances."""
    su = StellarUnicorn()
    graphics = PicoGraphics(display=DISPLAY_STELLAR_UNICORN)

    su.set_brightness(DEFAULT_BRIGHTNESS)
    sound.set_volume(su, VOLUME)

    buttons.init(su)
    bma400.init()
    sleep.init()

    return su, graphics


def check_brightness_buttons(su):
    """
    Check and handle the Stellar Unicorn's built-in brightness buttons.
    Returns True if a brightness button was pressed.
    """
    brightness_changed = False
    current = su.get_brightness()

    if su.is_pressed(StellarUnicorn.SWITCH_BRIGHTNESS_UP):
        su.set_brightness(min(MAX_BRIGHTNESS, current + 0.1))
        brightness_changed = True

    if su.is_pressed(StellarUnicorn.SWITCH_BRIGHTNESS_DOWN):
        su.set_brightness(max(MIN_BRIGHTNESS, current - 0.1))
        brightness_changed = True

    return brightness_changed


def create_interrupt_checker(su):
    """Create a closure that checks for button interrupts during animations."""
    def check_interrupt():
        check_brightness_buttons(su)
        return buttons.get_pressed()
    return check_interrupt


def run_ball_mode(su, graphics):
    """
    Enter tilt-ball mode. Runs until double-tap or button press.
    Returns the name of any button pressed during the game (to queue its
    animation on return), or None if exited via double-tap.
    """
    from games import tilt_ball

    print("Entering ball mode")
    sleep.reset_timer()

    # Capture which button (if any) ended the game
    exit_button = [None]

    def check_exit():
        sleep.reset_timer()  # movement keeps toy awake
        if bma400.double_tap_detected():
            return True
        b = buttons.get_pressed()
        if b:
            exit_button[0] = b
            return True
        return False

    tilt_ball.run(su, graphics, check_exit)

    print("Exiting ball mode (button={})".format(exit_button[0]))
    sleep.reset_timer()
    return exit_button[0]


def main():
    """Main program loop."""
    su, graphics = setup()

    print("Playing boot animation...")
    play_boot(su, graphics)

    display.clear(graphics, su)
    print("Ready - waiting for button press or double-tap...")

    next_button = None

    while True:
        # Auto-sleep
        if sleep.should_sleep():
            print("Entering sleep mode...")
            sleep.enter_sleep(su, graphics)
            print("Woke from sleep")
            next_button = None
            continue

        # Double-tap → ball mode
        if bma400.double_tap_detected():
            sound.stop(su)
            queued = run_ball_mode(su, graphics)
            next_button = queued  # play animation if a button ended the game
            continue

        check_brightness_buttons(su)

        # Button animation mode
        pressed = next_button or buttons.get_pressed()
        next_button = None

        if pressed:
            print(f"Button pressed: {pressed}")
            sleep.reset_timer()

            animation = get_animation(pressed)
            if animation:
                sound.stop(su)
                check_interrupt = create_interrupt_checker(su)
                interrupted_by = animation.play(su, graphics, check_interrupt)

                if interrupted_by:
                    print(f"Animation {pressed} interrupted by {interrupted_by}")
                    next_button = interrupted_by
                else:
                    print(f"Animation {pressed} completed")
                    display.clear(graphics, su)

                sleep.reset_timer()

        time.sleep_ms(10)


if __name__ == "__main__":
    main()
