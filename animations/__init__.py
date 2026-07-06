"""
Animation registry - maps button names to animation modules.
"""

from animations import boot, heart, star, rocket, butterfly, boat, green_test

# Map button names to animation modules
ANIMATIONS = {
    'heart':     heart,
    'star':      star,
    'rocket':    rocket,
    'butterfly': green_test,   # pink button → green/blue colour test
    'boat':      boat,
    'black':     butterfly,    # black button → butterfly animation
}


def get_animation(name):
    """Get the animation module for a button name."""
    return ANIMATIONS.get(name)


def play_boot(su, graphics, check_interrupt=None):
    """Play the boot animation."""
    return boot.play(su, graphics, check_interrupt)
