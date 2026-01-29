"""
Butterfly animation - colorful butterfly with flapping wings.
Plays for ~5 seconds with heartbeat sound, then holds final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/heartbeat.wav"


def get_butterfly_pixels(cx, cy, wing_angle, size=5):
    """
    Generate butterfly pixels with wings at given angle.

    Args:
        cx, cy: Center of butterfly body
        wing_angle: Angle of wings (0 = flat, higher = more raised)
        size: Size multiplier

    Returns:
        List of (x, y, r, g, b) tuples for colored pixels
    """
    pixels = []

    # Wing colors - bright and colorful
    colors = [
        (255, 50, 150),   # Pink
        (255, 100, 50),   # Orange
        (255, 255, 0),    # Yellow
        (100, 200, 255),  # Light blue
        (200, 100, 255),  # Purple
    ]

    # Body (dark brown/black)
    body_color = (40, 20, 10)

    # Draw body (vertical line in center)
    for dy in range(-3, 4):
        y = int(cy + dy)
        if 0 <= y < 16:
            pixels.append((int(cx), y, *body_color))

    # Wing spread based on angle (0.3 to 1.0)
    spread = 0.5 + 0.5 * math.sin(wing_angle)

    # Upper wings (larger)
    upper_wing_width = int(4 * spread) + 2
    upper_wing_height = 4

    for side in [-1, 1]:  # Left and right
        for wy in range(upper_wing_height):
            # Wing gets narrower towards top
            row_width = upper_wing_width - wy // 2
            for wx in range(1, row_width + 1):
                x = int(cx + side * wx)
                y = int(cy - 2 + wy - int(spread * 2))
                if 0 <= x < 16 and 0 <= y < 16:
                    # Color based on distance from body
                    color_idx = min(wx - 1, len(colors) - 1)
                    pixels.append((x, y, *colors[color_idx]))

    # Lower wings (smaller, rounder)
    lower_wing_width = int(3 * spread) + 1
    lower_wing_height = 3

    for side in [-1, 1]:
        for wy in range(lower_wing_height):
            row_width = lower_wing_width - abs(wy - 1)
            for wx in range(1, row_width + 1):
                x = int(cx + side * wx)
                y = int(cy + 1 + wy)
                if 0 <= x < 16 and 0 <= y < 16:
                    color_idx = min(wx - 1, len(colors) - 1)
                    # Slightly different colors for lower wings
                    c = colors[(color_idx + 2) % len(colors)]
                    pixels.append((x, y, *c))

    # Wing spots (decorative dots)
    spot_color = (255, 255, 255)  # White spots
    for side in [-1, 1]:
        # Upper wing spot
        spot_x = int(cx + side * int(2 * spread + 1))
        spot_y = int(cy - 1 - int(spread))
        if 0 <= spot_x < 16 and 0 <= spot_y < 16:
            pixels.append((spot_x, spot_y, *spot_color))
        # Lower wing spot
        spot_x = int(cx + side * int(1.5 * spread + 1))
        spot_y = int(cy + 2)
        if 0 <= spot_x < 16 and 0 <= spot_y < 16:
            pixels.append((spot_x, spot_y, *spot_color))

    # Antennae
    antenna_color = (60, 30, 15)
    for side in [-1, 1]:
        ax = int(cx + side)
        ay = int(cy - 4)
        if 0 <= ax < 16 and 0 <= ay < 16:
            pixels.append((ax, ay, *antenna_color))

    return pixels


def play(su, graphics, check_interrupt=None):
    """
    Play the butterfly flapping animation.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns button name if pressed

    Returns:
        None if completed normally, button name (str) if interrupted
    """
    # Random color variation
    color_shift = random.randint(0, 4)

    # Flap speed variation
    flap_speed = 4.0 + random.uniform(-0.5, 0.5)

    # Start sound
    sound.play(su, SOUND_FILE)

    # Animation phase (5 seconds)
    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    # Butterfly position - centered
    cx, cy = 8, 8

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            sound.stop(su)
            return interrupted_by

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0

        # Wing flapping angle
        wing_angle = t * flap_speed * math.pi

        # Slight vertical bobbing
        bob = math.sin(t * 2) * 0.5

        # Clear display
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        # Get and draw butterfly pixels
        pixels = get_butterfly_pixels(cx, cy + bob, wing_angle)
        for x, y, r, g, b in pixels:
            graphics.set_pen(graphics.create_pen(r, g, b))
            graphics.pixel(int(x), int(y))

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps

    # Hold phase (5 seconds) - wings spread
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    # Draw butterfly with wings spread (angle = pi/2 for max spread)
    pixels = get_butterfly_pixels(cx, cy, math.pi / 2)
    for x, y, r, g, b in pixels:
        graphics.set_pen(graphics.create_pen(r, g, b))
        graphics.pixel(int(x), int(y))

    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None  # Completed normally
