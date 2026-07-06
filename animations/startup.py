"""
Startup animation - plays the boot splash then holds the final frame.
Triggered by the black button (GPB4).
"""

from animations import boot

HOLD_MS = 20_000  # 20 seconds


def play(su, graphics, check_interrupt=None):
    return boot.play(su, graphics, check_interrupt, hold_ms=HOLD_MS)
