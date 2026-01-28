"""
Heart animation - a pink beating/pulsing heart.
Plays for ~5 seconds with heartbeat sound, then holds final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/heartbeat.wav"

# Heart shape templates at different scales
# Centered on 16x16 grid

def get_heart_pixels(scale=1.0, offset_x=0, offset_y=0):
    """
    Generate heart shape pixels using mathematical formula.
    Scale 1.0 = normal size, >1 = larger, <1 = smaller.
    """
    pixels = []
    cx, cy = 7.5, 8  # Center point

    for y in range(16):
        for x in range(16):
            # Normalize coordinates to -1 to 1 range, adjusted for scale
            nx = (x - cx) / (6 * scale)
            ny = (cy - y) / (6 * scale)  # Flip Y so heart points down

            # Heart equation: (x^2 + y^2 - 1)^3 - x^2 * y^3 < 0
            val = (nx * nx + ny * ny - 1) ** 3 - nx * nx * ny * ny * ny

            if val < 0:
                px = x + offset_x
                py = y + offset_y
                if 0 <= px < 16 and 0 <= py < 16:
                    pixels.append((px, py))

    return pixels


def play(su, graphics, check_interrupt=None):
    """
    Play the heart beating animation.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns True if animation should stop

    Returns:
        True if completed normally, False if interrupted
    """
    # Random variations per PRD
    base_pink = (255, 105, 180)  # Hot pink
    hue_shift = random.randint(-15, 15)
    r = min(255, max(0, base_pink[0] + hue_shift))
    g = min(255, max(0, base_pink[1] + hue_shift // 2))
    b = min(255, max(0, base_pink[2] - hue_shift // 2))

    beat_speed = 1.0 + random.uniform(-0.15, 0.15)

    # Start sound
    sound.play(su, SOUND_FILE)

    # Animation phase (5 seconds)
    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    frame = 0
    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        if check_interrupt and check_interrupt():
            sound.stop(su)
            return False

        # Calculate beat phase (pulsing effect)
        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        # Two-phase heartbeat: quick expand, slow contract
        beat_cycle = (t * beat_speed * 1.2) % 1.0

        if beat_cycle < 0.15:
            # First beat - quick expand
            scale = 1.0 + 0.15 * (beat_cycle / 0.15)
        elif beat_cycle < 0.25:
            # Contract
            scale = 1.15 - 0.15 * ((beat_cycle - 0.15) / 0.1)
        elif beat_cycle < 0.35:
            # Second beat - smaller expand
            scale = 1.0 + 0.1 * ((beat_cycle - 0.25) / 0.1)
        elif beat_cycle < 0.5:
            # Contract back
            scale = 1.1 - 0.1 * ((beat_cycle - 0.35) / 0.15)
        else:
            # Rest phase
            scale = 1.0

        # Clear and draw heart
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        pixels = get_heart_pixels(scale)
        pen = graphics.create_pen(r, g, b)
        graphics.set_pen(pen)

        for x, y in pixels:
            graphics.pixel(x, y)

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps
        frame += 1

    # Hold phase (5 seconds) - show final heart
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    pixels = get_heart_pixels(1.0)
    pen = graphics.create_pen(r, g, b)
    graphics.set_pen(pen)
    for x, y in pixels:
        graphics.pixel(x, y)
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        if check_interrupt and check_interrupt():
            return False
        time.sleep_ms(50)

    return True
