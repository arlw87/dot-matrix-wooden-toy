"""
Dot Matrix Wooden Toy - Main Program
=====================================
An interactive toy for toddlers featuring a 16x16 RGB LED matrix.
Six push-to-make buttons (wired to MCP23017 GPB0-GPB5) each trigger
a different animation: heart, star, moon, flower, butterfly, boot.

Hardware: Pimoroni Stellar Unicorn with Raspberry Pi Pico 2 W + MCP23017
"""

import gc
gc.collect()  # Clean memory before any allocations

# CRITICAL: Import sound FIRST to allocate audio buffer before fragmentation
from lib import sound

import time
from machine import I2C, Pin
from stellar import StellarUnicorn
from picographics import PicoGraphics, DISPLAY_STELLAR_UNICORN

# Import remaining modules
from lib import display, buttons, sleep
from lib.kx134 import KX134
from animations import get_animation, play_boot
from games import tilt

# Configuration
DEFAULT_BRIGHTNESS = 1  # 75% brightness
MIN_BRIGHTNESS = 0.1      # Minimum brightness floor
MAX_BRIGHTNESS = 1.0
VOLUME = 0.45             # Fixed moderate volume (~45%)


def setup():
    """Initialize hardware and return instances."""
    print("[SETUP] Creating display...")
    su = StellarUnicorn()
    graphics = PicoGraphics(display=DISPLAY_STELLAR_UNICORN)

    print("[SETUP] Setting brightness and volume...")
    su.set_brightness(DEFAULT_BRIGHTNESS)
    sound.set_volume(su, VOLUME)

    print("[SETUP] Initialising buttons (MCP23017)...")
    buttons.init(su)
    print("[SETUP] Buttons OK")

    print("[SETUP] Initialising sleep timer...")
    sleep.init()

    print("[SETUP] Initialising KX134 accelerometer...")
    kx = None
    try:
        kx_i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
        devices = kx_i2c.scan()
        print(f"[SETUP] I2C scan found devices: {[hex(d) for d in devices]}")
        kx = KX134(kx_i2c)
        print("[SETUP] KX134 OK — X/Y/Z measurement enabled")
    except Exception as e:
        print(f"[SETUP] KX134 FAILED: {e} — accelerometer disabled")

    return su, graphics, kx


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
        # Hold-to-delay audio: once the trigger button is released, let the
        # animation's deferred sound start.
        if not buttons.any_pressed():
            sound.release_gate(su)
        return buttons.get_pressed()

    return check_interrupt


def play_tilt_game(su, graphics, kx):
    """
    Run the Tilt Game as a blocking loop until the player exits (holds
    yellow+red for 5s again) or the ball settles and the toy sleeps.

    While in the game the Animation Buttons are ignored — tilt.run() only reads
    the KX134 and the exit gesture.
    """
    print("[MODE] Yellow + Red held 5s → entering Tilt Game")
    sound.stop(su)
    display.clear(graphics, su)

    if kx is None:
        print("[TILT] No KX134 — cannot run Tilt Game; returning to Animation Mode")
        return

    # Exit when the yellow+red combo is held for 5s again. check_mode_toggle()
    # won't re-fire until the entry hold is released first (its fired-latch).
    outcome = tilt.run(su, graphics, kx, should_exit=buttons.check_mode_toggle)

    display.clear(graphics, su)
    buttons.reset_mode_toggle()

    if outcome == tilt.SLEEP:
        print("[MODE] Tilt Game settled (held still) → entering sleep")
        sleep.enter_sleep(su, graphics)
        print("[MODE] Woke from sleep → Animation Mode")
    else:
        print("[MODE] Exited Tilt Game → Animation Mode")

    sleep.reset_timer()


def main():
    """Main program loop."""
    print("=== TOY STARTING ===")
    su, graphics, kx = setup()
    print("[SETUP] All done")

    print("[MAIN] Playing boot animation...")
    play_boot(su, graphics)

    display.clear(graphics, su)
    print("[MAIN] Ready — waiting for button press")

    next_button = None
    _last_kx_print = time.ticks_ms()
    _last_heartbeat = time.ticks_ms()

    while True:
        # Check for auto-sleep
        if sleep.should_sleep():
            print("Entering sleep mode...")
            sleep.enter_sleep(su, graphics)
            print("Woke from sleep")
            # After wake, just go back to idle (no boot animation per PRD)
            next_button = None
            buttons.reset_mode_toggle()
            continue

        # Mode toggle: hold the yellow (star) + red (heart) buttons together for
        # 5 seconds to enter the Tilt Game. The game runs as a blocking loop;
        # holding the same combo again (or the ball settling) exits it.
        if buttons.check_mode_toggle():
            play_tilt_game(su, graphics, kx)
            next_button = None
            continue

        now = time.ticks_ms()

        # ── Animation Mode ────────────────────────────────────────────────────
        # Handle brightness buttons
        check_brightness_buttons(su)

        # While the yellow+red toggle combo is being held, don't fire an
        # animation — let the hold accumulate toward the mode toggle instead.
        if buttons.is_pressed('star') and buttons.is_pressed('heart'):
            time.sleep_ms(10)
            continue

        # Check for button press (use queued button or poll for new one)
        pressed = next_button or buttons.get_pressed()
        next_button = None  # Clear queued button

        if pressed:
            print(f"[BTN] {pressed} pressed")
            sleep.reset_timer()

            # Get the animation for this button
            animation = get_animation(pressed)

            if animation:
                # Stop any playing sound
                sound.stop(su)

                # Defer this animation's audio until the trigger button is
                # released. The interrupt checker opens the gate on button-up;
                # if the button is only tapped, the gate opens on the next frame.
                sound.arm_gate()

                # Create interrupt checker
                check_interrupt = create_interrupt_checker(su)

                # Play the animation - returns None if completed, or button name if interrupted
                interrupted_by = animation.play(su, graphics, check_interrupt)

                # Animation over — don't leak deferred audio into the next one
                sound.disarm_gate()

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

        # Heartbeat so you can tell the loop is alive
        if time.ticks_diff(now, _last_heartbeat) >= 5000:
            print("[MAIN] loop alive")
            _last_heartbeat = now

        # KX134 accelerometer — periodic X/Y/Z readout
        if kx:
            if time.ticks_diff(now, _last_kx_print) >= 500:
                x, y, z = kx.read_xyz()
                print(f"[KX134] X={x:+.3f}g  Y={y:+.3f}g  Z={z:+.3f}g")
                _last_kx_print = now

        # Small delay to prevent busy-waiting
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
