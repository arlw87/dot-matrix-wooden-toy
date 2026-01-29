"""
Flower animation - a flower grows from the bottom and blooms.
Plays for ~5 seconds with nature sound, then holds final frame for 5 seconds.
"""

import time
import math
import random
from lib import display, sound

SOUND_FILE = "sounds/flower.wav"


def play(su, graphics, check_interrupt=None):
    """
    Play the growing flower animation.

    Args:
        su: Stellar Unicorn instance
        graphics: PicoGraphics instance
        check_interrupt: Optional callback that returns button name if pressed

    Returns:
        None if completed normally, button name (str) if interrupted
    """
    # Random variations
    petal_colors = [
        (255, 100, 150),  # Pink
        (255, 80, 80),    # Red
        (255, 150, 50),   # Orange
        (200, 100, 255),  # Purple
        (255, 200, 100),  # Yellow
    ]
    petal_color = random.choice(petal_colors)

    # Slight color variation
    petal_color = (
        min(255, max(0, petal_color[0] + random.randint(-20, 20))),
        min(255, max(0, petal_color[1] + random.randint(-20, 20))),
        min(255, max(0, petal_color[2] + random.randint(-20, 20)))
    )

    stem_color = (34, 139, 34)  # Forest green
    center_color = (255, 200, 50)  # Yellow center
    leaf_color = (50, 180, 50)  # Lighter green for leaves

    growth_speed = 1.0 + random.uniform(-0.15, 0.15)
    num_petals = random.choice([5, 6, 7])

    # Stem position
    stem_x = 7
    stem_bottom = 15
    stem_top = 5  # Where flower will bloom

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
        progress = min(1.0, t * growth_speed / 4.0)  # Full growth in ~4 seconds

        # Clear display
        graphics.set_pen(graphics.create_pen(0, 0, 0))
        graphics.clear()

        # Phase 1: Stem grows (0-40% of animation)
        stem_progress = min(1.0, progress / 0.4)
        stem_height = int((stem_bottom - stem_top) * stem_progress)
        current_stem_top = stem_bottom - stem_height

        # Draw stem
        graphics.set_pen(graphics.create_pen(*stem_color))
        for y in range(current_stem_top, stem_bottom + 1):
            graphics.pixel(stem_x, y)
            # Thicker stem at bottom
            if y > stem_bottom - 3:
                graphics.pixel(stem_x + 1, y)

        # Phase 2: Leaves appear (20-60% of animation)
        if progress > 0.2:
            leaf_progress = min(1.0, (progress - 0.2) / 0.4)
            graphics.set_pen(graphics.create_pen(*leaf_color))

            # Left leaf
            leaf_y = stem_bottom - 4
            if current_stem_top <= leaf_y:
                leaf_size = int(3 * leaf_progress)
                for i in range(leaf_size):
                    graphics.pixel(stem_x - 1 - i, leaf_y + i)
                    if i > 0:
                        graphics.pixel(stem_x - 1 - i, leaf_y + i - 1)

            # Right leaf (slightly higher)
            leaf_y2 = stem_bottom - 7
            if current_stem_top <= leaf_y2:
                for i in range(leaf_size):
                    graphics.pixel(stem_x + 1 + i, leaf_y2 + i)
                    if i > 0:
                        graphics.pixel(stem_x + 1 + i, leaf_y2 + i - 1)

        # Phase 3: Flower blooms (50-100% of animation)
        if progress > 0.5:
            bloom_progress = (progress - 0.5) / 0.5
            flower_cx = stem_x + 0.5
            flower_cy = stem_top

            # Draw petals
            graphics.set_pen(graphics.create_pen(*petal_color))
            petal_radius = 3 * bloom_progress

            for i in range(num_petals):
                angle = (i / num_petals) * 2 * math.pi - math.pi / 2
                # Petal center position
                px = flower_cx + math.cos(angle) * petal_radius * 0.7
                py = flower_cy + math.sin(angle) * petal_radius * 0.7

                # Draw petal as small filled area
                petal_size = max(1, int(petal_radius * 0.8))
                for dy in range(-petal_size, petal_size + 1):
                    for dx in range(-petal_size, petal_size + 1):
                        if dx * dx + dy * dy <= petal_size * petal_size:
                            x = int(px + dx)
                            y = int(py + dy)
                            if 0 <= x < 16 and 0 <= y < 16:
                                graphics.pixel(x, y)

            # Draw center
            if bloom_progress > 0.3:
                center_progress = (bloom_progress - 0.3) / 0.7
                graphics.set_pen(graphics.create_pen(*center_color))
                center_size = max(1, int(2 * center_progress))
                for dy in range(-center_size, center_size + 1):
                    for dx in range(-center_size, center_size + 1):
                        if dx * dx + dy * dy <= center_size * center_size:
                            x = int(flower_cx + dx)
                            y = int(flower_cy + dy)
                            if 0 <= x < 16 and 0 <= y < 16:
                                graphics.pixel(x, y)

        su.update(graphics)
        time.sleep_ms(33)  # ~30 fps

    # Hold phase - draw final bloomed flower
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    # Final stem
    graphics.set_pen(graphics.create_pen(*stem_color))
    for y in range(stem_top, stem_bottom + 1):
        graphics.pixel(stem_x, y)
        if y > stem_bottom - 3:
            graphics.pixel(stem_x + 1, y)

    # Final leaves
    graphics.set_pen(graphics.create_pen(*leaf_color))
    leaf_y = stem_bottom - 4
    for i in range(3):
        graphics.pixel(stem_x - 1 - i, leaf_y + i)
        if i > 0:
            graphics.pixel(stem_x - 1 - i, leaf_y + i - 1)

    leaf_y2 = stem_bottom - 7
    for i in range(3):
        graphics.pixel(stem_x + 1 + i, leaf_y2 + i)
        if i > 0:
            graphics.pixel(stem_x + 1 + i, leaf_y2 + i - 1)

    # Final petals
    flower_cx = stem_x + 0.5
    flower_cy = stem_top
    petal_radius = 3

    graphics.set_pen(graphics.create_pen(*petal_color))
    for i in range(num_petals):
        angle = (i / num_petals) * 2 * math.pi - math.pi / 2
        px = flower_cx + math.cos(angle) * petal_radius * 0.7
        py = flower_cy + math.sin(angle) * petal_radius * 0.7
        petal_size = int(petal_radius * 0.8)
        for dy in range(-petal_size, petal_size + 1):
            for dx in range(-petal_size, petal_size + 1):
                if dx * dx + dy * dy <= petal_size * petal_size:
                    x = int(px + dx)
                    y = int(py + dy)
                    if 0 <= x < 16 and 0 <= y < 16:
                        graphics.pixel(x, y)

    # Final center
    graphics.set_pen(graphics.create_pen(*center_color))
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx * dx + dy * dy <= 4:
                x = int(flower_cx + dx)
                y = int(flower_cy + dy)
                if 0 <= x < 16 and 0 <= y < 16:
                    graphics.pixel(x, y)

    su.update(graphics)

    hold_start = time.ticks_ms()
    hold_duration_ms = 5000

    while time.ticks_diff(time.ticks_ms(), hold_start) < hold_duration_ms:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None  # Completed normally
