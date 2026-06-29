"""
Colour test - static palette displayed for 20 seconds.
Shows 16 colour blocks (4x4 pixels each) across the 16x16 matrix
so you can judge which colours are visible on the physical display.
"""

import time
from lib import display

DURATION_MS = 20000  # 20 seconds on screen

# 4x4 grid of colour blocks, read left-to-right then top-to-bottom.
# Covers the full spectrum plus warm/cool shades and neutrals.
COLOURS = [
    # Row 0  (top)
    (255,   0,   0),   # Red
    (255, 128,   0),   # Orange
    (255, 255,   0),   # Yellow
    (255, 255, 255),   # White
    # Row 1
    (128,   0,   0),   # Dark red
    (255, 192,   0),   # Amber
    (128, 255,   0),   # Lime
    (128, 128, 128),   # Grey
    # Row 2
    (  0, 255,   0),   # Green
    (  0, 255, 255),   # Cyan
    (  0,   0, 255),   # Blue
    (255,   0, 255),   # Magenta
    # Row 3  (bottom)
    (  0, 128,   0),   # Dark green
    (  0, 128, 128),   # Teal
    (  0,   0, 128),   # Navy
    (128,   0, 128),   # Purple
]


def play(su, graphics, check_interrupt=None):
    """Display the colour test grid for 20 seconds."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    for i, (r, g, b) in enumerate(COLOURS):
        block_col = i % 4
        block_row = i // 4
        graphics.set_pen(graphics.create_pen(r, g, b))
        for dy in range(4):
            for dx in range(4):
                display.pixel(graphics, block_col * 4 + dx, block_row * 4 + dy)

    su.update(graphics)

    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < DURATION_MS:
        interrupted_by = check_interrupt() if check_interrupt else None
        if interrupted_by:
            return interrupted_by
        time.sleep_ms(50)

    return None
