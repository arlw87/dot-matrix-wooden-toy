"""
Star animation - a yellow bouncing and rotating star.
Plays for ~5 seconds with sparkle sound, then holds final frame for 5 seconds.
Star occupies roughly 70% of the display area.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/star.wav"


def get_star_pixels(cx, cy, size, rotation, num_points=5):
    """
    Generate a star shape centered at (cx, cy).

    Args:
        cx, cy: Center coordinates
        size: Outer radius of the star
        rotation: Rotation angle in radians
        num_points: Number of star points (default 5)

    Returns:
        List of (x, y) pixel coordinates
    """
    pixels = set()

    outer_radius = size
    inner_radius = size * 0.4  # Inner radius is 40% of outer

    # Generate star vertices
    vertices = []
    for i in range(num_points * 2):
        angle = rotation + (i * math.pi / num_points) - math.pi / 2
        if i % 2 == 0:
            r = outer_radius
        else:
            r = inner_radius
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        vertices.append((x, y))

    # Fill the star using scanline approach
    # First, find bounding box
    min_y = int(min(v[1] for v in vertices))
    max_y = int(max(v[1] for v in vertices))

    for y in range(max(0, min_y), min(16, max_y + 1)):
        # Find intersections with star edges
        intersections = []
        for i in range(len(vertices)):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % len(vertices)]

            if (v1[1] <= y < v2[1]) or (v2[1] <= y < v1[1]):
                if v2[1] != v1[1]:
                    x = v1[0] + (y - v1[1]) * (v2[0] - v1[0]) / (v2[1] - v1[1])
                    intersections.append(x)

        intersections.sort()

        # Fill between pairs of intersections
        for i in range(0, len(intersections) - 1, 2):
            x_start = int(intersections[i])
            x_end = int(intersections[i + 1])
            for x in range(max(0, x_start), min(16, x_end + 1)):
                pixels.add((x, y))

    return list(pixels)


def play(su, graphics, check_interrupt=None):
    """
    Play the star bouncing and rotating animation.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns True if animation should stop

    Returns:
        True if completed normally, False if interrupted
    """
    # Random variations per PRD
    base_yellow = (255, 220, 0)
    hue_shift = random.randint(-20, 20)
    r = min(255, max(0, base_yellow[0] + hue_shift))
    g = min(255, max(0, base_yellow[1] + hue_shift))
    b = min(255, max(0, base_yellow[2]))

    # Rotation direction and speed variation
    rotation_dir = random.choice([-1, 1])
    rotation_speed = (0.8 + random.uniform(-0.15, 0.15)) * rotation_dir
    bounce_speed = 1.0 + random.uniform(-0.15, 0.15)

    # Star size: 70% of display = radius of about 5-6 pixels
    star_size = 5.5

    # Start sound
    sound.play(su, SOUND_FILE)

    # Animation phase (5 seconds)
    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    final_rotation = 0
    final_y = 7.5

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        if check_interrupt and check_interrupt():
            sound.stop(su)
            return False

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0

        # Rotation
        rotation = t * rotation_speed * 2

        # Bouncing motion (sinusoidal)
        bounce_offset = math.sin(t * bounce_speed * 4) * 2.5
        cy = 7.5 + bounce_offset

        # Save for final frame
        final_rotation = rotation
        final_y = cy

        # Clear and draw star
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        pixels = get_star_pixels(7.5, cy, star_size, rotation)
        pen = graphics.create_pen(r, g, b)
        graphics.set_pen(pen)

        for x, y in pixels:
            if 0 <= x < 16 and 0 <= y < 16:
                graphics.pixel(int(x), int(y))

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps

    # Hold phase (5 seconds) - show star at center, no rotation
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    pixels = get_star_pixels(7.5, 7.5, star_size, 0)
    pen = graphics.create_pen(r, g, b)
    graphics.set_pen(pen)
    for x, y in pixels:
        if 0 <= x < 16 and 0 <= y < 16:
            graphics.pixel(int(x), int(y))
    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        if check_interrupt and check_interrupt():
            return False
        time.sleep_ms(50)

    return True
