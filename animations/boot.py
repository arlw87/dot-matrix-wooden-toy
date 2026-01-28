"""
Boot splash animation - colorful display on power-on.
Plays for 1-2 seconds to indicate successful power-up.
"""

import time
import math
from lib import display, sound

SOUND_FILE = "sounds/startup.wav"


def play(su, graphics, check_interrupt=None):
    """
    Play the boot splash animation.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns True if animation should stop

    Returns:
        True if completed, False if interrupted
    """
    # Start the boot sound
    sound.play(su, SOUND_FILE)

    # Rainbow wave animation - colorful and engaging
    start_time = time.ticks_ms()
    duration_ms = 1500  # 1.5 seconds

    frame = 0
    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        # Check for interrupt
        if check_interrupt and check_interrupt():
            sound.stop(su)
            return False

        # Clear display
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        # Draw expanding rainbow rings from center
        cx, cy = 7.5, 7.5  # Center of 16x16 grid

        for y in range(16):
            for x in range(16):
                # Distance from center
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)

                # Create rainbow based on distance and time
                hue = (dist * 20 + frame * 5) % 360

                # Only draw pixels within expanding radius
                max_radius = (frame / 2) % 12
                if dist <= max_radius + 2:
                    r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                    graphics.set_pen(graphics.create_pen(r, g, b))
                    graphics.pixel(x, y)

        su.update(graphics)
        frame += 1
        time.sleep_ms(33)  # ~30 fps

    # Brief pause on final frame
    time.sleep_ms(200)

    # Clear display
    display.clear(graphics, su)

    return True


def hsv_to_rgb(h, s, v):
    """Convert HSV (hue 0-360, sat 0-1, val 0-1) to RGB (0-255)."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
