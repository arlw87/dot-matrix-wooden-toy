"""
Animation registry - maps button names to animation modules.
"""

from animations import boot, heart, star, fish, bee, butterfly, colour_test

# Map button names to animation modules
ANIMATIONS = {
    'heart':     heart,
    'star':      star,
    'fish':      fish,
    'bee':       bee,
    'butterfly': butterfly,
    'boot':      colour_test,
}


def get_animation(name):
    """Get the animation module for a button name."""
    return ANIMATIONS.get(name)


def play_boot(su, graphics, check_interrupt=None):
    """Play the boot animation."""
    return boot.play(su, graphics, check_interrupt)
