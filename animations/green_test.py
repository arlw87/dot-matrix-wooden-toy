"""
Green & greeny-blue colour test — static palette for hardware comparison.
Triggered by the black button (GPB4). Stays on screen for 20 seconds.
"""

import time
from lib import display

DURATION_MS = 20_000

# 4×4 grid of 4×4-pixel blocks, left-to-right then top-to-bottom.
# Columns progress from pure green → cyan; rows vary brightness and yellow-bias.
COLOURS = [
    # Row 0 — full brightness, green → cyan
    (  0, 255,   0),   # Pure Green
    (  0, 255,  64),   # Green-Mint
    (  0, 255, 128),   # Spring Green
    (  0, 255, 255),   # Cyan
    # Row 1 — lime family (yellow bias via red channel)
    ( 64, 255,   0),   # Lime-Green
    (128, 255,   0),   # Lime
    (200, 255,   0),   # Yellow-Lime
    (  0, 255, 200),   # Near-Cyan
    # Row 2 — medium brightness (G=200)
    (  0, 200,   0),   # Mid Green
    (  0, 200, 100),   # Mid Spring
    (  0, 200, 200),   # Mid Cyan
    (  0, 200, 255),   # Aqua
    # Row 3 — aquas and turquoise
    (  0, 255,  96),   # Mint
    (  0, 230, 150),   # Sea Green
    ( 64, 220, 200),   # Turquoise
    (  0, 160, 255),   # Blue-Green
]


def play(su, graphics, check_interrupt=None):
    """Display the green/blue-green test grid for 20 seconds."""
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
