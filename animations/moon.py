"""
Moon/Night Sky animation - moon and stars fade in, then a shooting star crosses.
Plays for ~5 seconds with chime sound, then holds final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/moon.wav"


def get_moon_pixels(cx, cy, radius):
    """Generate a crescent moon shape."""
    pixels = []
    for y in range(16):
        for x in range(16):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            # Main circle
            if dist <= radius:
                # Cut out inner circle offset to create crescent
                inner_cx = cx + radius * 0.5
                inner_dist = math.sqrt((x - inner_cx) ** 2 + dy * dy)
                if inner_dist > radius * 0.85:
                    pixels.append((x, y))
    return pixels


def play(su, graphics, check_interrupt=None):
    """
    Play the night sky animation with moon, stars, and shooting star.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns True if animation should stop

    Returns:
        True if completed normally, False if interrupted
    """
    # Random variations
    moon_brightness = random.randint(200, 255)
    num_stars = random.randint(8, 15)

    # Generate random star positions (avoiding moon area)
    moon_cx, moon_cy = 11, 4
    moon_radius = 3

    stars = []
    for _ in range(num_stars):
        attempts = 0
        while attempts < 20:
            x = random.randint(0, 15)
            y = random.randint(0, 15)
            # Avoid moon area
            dx = x - moon_cx
            dy = y - moon_cy
            if math.sqrt(dx * dx + dy * dy) > moon_radius + 2:
                stars.append({
                    'x': x,
                    'y': y,
                    'brightness': random.randint(100, 255),
                    'twinkle_offset': random.uniform(0, 2 * math.pi)
                })
                break
            attempts += 1

    # Shooting star parameters
    shoot_start_x = random.randint(0, 5)
    shoot_start_y = random.randint(0, 3)
    shoot_angle = random.uniform(0.3, 0.8)  # Diagonal down-right
    shoot_speed = random.uniform(3, 5)
    shoot_time = random.uniform(2.5, 3.5)  # When shooting star appears

    # Colors
    moon_color = (moon_brightness, moon_brightness, int(moon_brightness * 0.9))
    bg_color = (5, 5, 20)  # Dark blue night sky

    # Start sound
    sound.play(su, SOUND_FILE)

    # Animation phase (5 seconds)
    start_time = time.ticks_ms()
    animation_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), start_time) < animation_duration_ms:
        if check_interrupt and check_interrupt():
            sound.stop(su)
            return False

        t = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0

        # Clear with dark blue background
        graphics.set_pen(graphics.create_pen(*bg_color))
        graphics.clear()

        # Fade in factor (0 to 1 over first 1.5 seconds)
        fade_in = min(1.0, t / 1.5)

        # Draw stars with twinkling
        for star in stars:
            twinkle = 0.7 + 0.3 * math.sin(t * 3 + star['twinkle_offset'])
            brightness = int(star['brightness'] * fade_in * twinkle)
            graphics.set_pen(graphics.create_pen(brightness, brightness, brightness))
            graphics.pixel(star['x'], star['y'])

        # Draw moon
        moon_pixels = get_moon_pixels(moon_cx, moon_cy, moon_radius)
        r = int(moon_color[0] * fade_in)
        g = int(moon_color[1] * fade_in)
        b = int(moon_color[2] * fade_in)
        graphics.set_pen(graphics.create_pen(r, g, b))
        for x, y in moon_pixels:
            graphics.pixel(x, y)

        # Draw shooting star if it's time
        if t >= shoot_time:
            shoot_t = t - shoot_time
            shoot_progress = shoot_t * shoot_speed

            # Shooting star head position
            head_x = shoot_start_x + shoot_progress * math.cos(shoot_angle) * 4
            head_y = shoot_start_y + shoot_progress * math.sin(shoot_angle) * 4

            # Draw tail (fading trail)
            tail_length = 4
            for i in range(tail_length):
                tail_x = head_x - i * math.cos(shoot_angle) * 0.8
                tail_y = head_y - i * math.sin(shoot_angle) * 0.8
                if 0 <= int(tail_x) < 16 and 0 <= int(tail_y) < 16:
                    brightness = int(255 * (1 - i / tail_length))
                    graphics.set_pen(graphics.create_pen(brightness, brightness, int(brightness * 0.8)))
                    graphics.pixel(int(tail_x), int(tail_y))

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps

    # Hold phase (5 seconds) - show final night sky without shooting star
    graphics.set_pen(graphics.create_pen(*bg_color))
    graphics.clear()

    # Draw stars (no twinkling during hold)
    for star in stars:
        graphics.set_pen(graphics.create_pen(star['brightness'], star['brightness'], star['brightness']))
        graphics.pixel(star['x'], star['y'])

    # Draw moon
    graphics.set_pen(graphics.create_pen(*moon_color))
    for x, y in moon_pixels:
        graphics.pixel(x, y)

    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        if check_interrupt and check_interrupt():
            return False
        time.sleep_ms(50)

    return True
