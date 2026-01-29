"""
Moon/Night Sky animation - full moon rises from bottom-left to center.
Plays for ~5 seconds with chime sound, then holds final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/moon.wav"


def get_moon_pixels(cx, cy, radius):
    """Generate a full moon shape."""
    pixels = []
    for y in range(16):
        for x in range(16):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist <= radius:
                pixels.append((x, y))
    return pixels


def play(su, graphics, check_interrupt=None):
    """
    Play the night sky animation with rising moon and twinkling stars.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns button name if pressed

    Returns:
        None if completed normally, button name (str) if interrupted
    """
    # Random variations
    moon_brightness = random.randint(200, 255)
    num_stars = random.randint(8, 15)

    # Full moon, slightly smaller
    moon_radius = 6
    # Moon rises from bottom-left (off screen) to center
    start_cx, start_cy = -3, 19
    end_cx, end_cy = 8, 8

    # Generate random star positions (avoiding final moon area at center)
    stars = []
    for _ in range(num_stars):
        attempts = 0
        while attempts < 20:
            x = random.randint(0, 15)
            y = random.randint(0, 15)
            # Avoid center where moon will end up
            dx = x - end_cx
            dy = y - end_cy
            if math.sqrt(dx * dx + dy * dy) > moon_radius + 1:
                stars.append({
                    'x': x,
                    'y': y,
                    'brightness': random.randint(100, 255),
                    'twinkle_offset': random.uniform(0, 2 * math.pi)
                })
                break
            attempts += 1

    # Colors
    moon_color = (moon_brightness, moon_brightness, int(moon_brightness * 0.9))
    bg_color = (5, 5, 20)  # Dark blue night sky

    # Start sound
    sound.play(su, SOUND_FILE)

    # Animation phase (5 seconds)
    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            sound.stop(su)
            return interrupted_by

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
        progress = min(1.0, t / 4.0)  # Moon reaches center in 4 seconds

        # Clear with dark blue background
        graphics.set_pen(graphics.create_pen(*bg_color))
        graphics.clear()

        # Only draw stars after moon reaches final position (t >= 4)
        if t >= 4.0:
            # Fade in stars over 1 second after moon arrives
            star_fade = min(1.0, (t - 4.0) / 1.0)
            for star in stars:
                twinkle = 0.7 + 0.3 * math.sin(t * 3 + star['twinkle_offset'])
                brightness = int(star['brightness'] * star_fade * twinkle)
                graphics.set_pen(graphics.create_pen(brightness, brightness, brightness))
                graphics.pixel(star['x'], star['y'])

        # Calculate moon position (rising from bottom-left to center)
        moon_cx = start_cx + (end_cx - start_cx) * progress
        moon_cy = start_cy + (end_cy - start_cy) * progress

        # Draw moon
        moon_pixels = get_moon_pixels(moon_cx, moon_cy, moon_radius)
        graphics.set_pen(graphics.create_pen(*moon_color))
        for x, y in moon_pixels:
            graphics.pixel(x, y)

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps

    # Hold phase (5 seconds) - moon at center, stars twinkling
    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    # Pre-calculate final moon pixels
    final_moon_pixels = get_moon_pixels(end_cx, end_cy, moon_radius)

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by

        t = time.ticks_diff(time.ticks_ms(), hold_start) / 1000.0

        graphics.set_pen(graphics.create_pen(*bg_color))
        graphics.clear()

        # Draw stars with twinkling during hold
        for star in stars:
            twinkle = 0.7 + 0.3 * math.sin(t * 3 + star['twinkle_offset'])
            brightness = int(star['brightness'] * twinkle)
            graphics.set_pen(graphics.create_pen(brightness, brightness, brightness))
            graphics.pixel(star['x'], star['y'])

        # Draw moon at center
        graphics.set_pen(graphics.create_pen(*moon_color))
        for x, y in final_moon_pixels:
            graphics.pixel(x, y)

        su.update(graphics)
        time.sleep_ms(50)

    return None  # Completed normally
