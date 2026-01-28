"""
Shared display helpers for the Stellar Unicorn 16x16 RGB LED matrix.
"""

def clear(graphics, su):
    """Clear the display to black."""
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    su.update(graphics)


def fill(graphics, su, r, g, b):
    """Fill the entire display with a solid colour."""
    graphics.set_pen(graphics.create_pen(r, g, b))
    graphics.clear()
    su.update(graphics)


def set_pixel(graphics, x, y, r, g, b):
    """Set a single pixel to a colour (does not update display)."""
    graphics.set_pen(graphics.create_pen(r, g, b))
    graphics.pixel(x, y)


def draw_sprite(graphics, sprite, offset_x=0, offset_y=0, r=255, g=255, b=255):
    """
    Draw a sprite (list of (x, y) tuples) at an offset with a given colour.
    Does not update display - call su.update(graphics) after.
    """
    pen = graphics.create_pen(r, g, b)
    graphics.set_pen(pen)
    for x, y in sprite:
        px = x + offset_x
        py = y + offset_y
        if 0 <= px < 16 and 0 <= py < 16:
            graphics.pixel(px, py)


def fade_to_black(graphics, su, steps=10, delay_ms=50):
    """
    Fade the current display to black over a number of steps.
    Note: This reads from a buffer, so it requires storing frame data.
    For simplicity, we just do a quick fade by dimming brightness.
    """
    import time
    original_brightness = su.get_brightness()
    for i in range(steps, -1, -1):
        brightness = original_brightness * (i / steps)
        su.set_brightness(brightness)
        su.update(graphics)
        time.sleep_ms(delay_ms)
    # Clear and restore brightness
    clear(graphics, su)
    su.set_brightness(original_brightness)


def lerp_color(r1, g1, b1, r2, g2, b2, t):
    """Linearly interpolate between two colours. t is 0.0 to 1.0."""
    return (
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t)
    )
