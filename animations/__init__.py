"""
Animation registry - maps button names to animation modules.
"""

from animations import boot, heart, star, moon, flower, butterfly

# Map button names to animation modules
# Note: 'moon' button now triggers butterfly (moon didn't look good on 16x16)
ANIMATIONS = {
    'heart': heart,
    'star': star,
    'moon': butterfly,  # Button C = butterfly
    'flower': flower,
    'butterfly': butterfly,
}


def get_animation(name):
    """Get the animation module for a button name."""
    return ANIMATIONS.get(name)


def play_boot(su, graphics, check_interrupt=None):
    """Play the boot animation."""
    return boot.play(su, graphics, check_interrupt)
