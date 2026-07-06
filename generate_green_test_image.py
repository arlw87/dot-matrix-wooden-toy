#!/usr/bin/env python3
"""
Generate a preview PNG for the green/greeny-blue colour test grid.
Matches the 4×4 block layout of animations/green_test.py.

Run from project root:  python3 generate_green_test_image.py
"""

from PIL import Image, ImageDraw, ImageFont

CELL = 22          # pixels per LED dot in the preview
PADDING = 6        # gap around each dot
LABEL_H = 18       # height reserved below each 4×4 block for the colour name
BLOCKS = 4         # blocks per row/column
LEDS = 4           # LEDs per block side

COLOURS = [
    # Row 0
    ((  0, 255,   0), "Pure Green"),
    ((  0, 255,  64), "Green-Mint"),
    ((  0, 255, 128), "Spring"),
    ((  0, 255, 255), "Cyan"),
    # Row 1
    (( 64, 255,   0), "Lime-Green"),
    ((128, 255,   0), "Lime"),
    ((200, 255,   0), "Yel-Lime"),
    ((  0, 255, 200), "Near-Cyan"),
    # Row 2
    ((  0, 200,   0), "Mid Green"),
    ((  0, 200, 100), "Mid Spring"),
    ((  0, 200, 200), "Mid Cyan"),
    ((  0, 200, 255), "Aqua"),
    # Row 3
    ((  0, 255,  96), "Mint"),
    ((  0, 230, 150), "Sea Green"),
    (( 64, 220, 200), "Turquoise"),
    ((  0, 160, 255), "Blue-Green"),
]

BLOCK_PX = LEDS * CELL          # pixel width/height of one colour block
TOTAL_W = BLOCKS * BLOCK_PX
TOTAL_H = BLOCKS * (BLOCK_PX + LABEL_H)

BG = (0, 0, 0)
DOT_MARGIN = 3     # gap between dot edge and cell edge


def draw_block(draw, bx, by, colour, label):
    """Draw a 4×4 grid of LED circles and a label below the block."""
    ox = bx * BLOCK_PX
    oy = by * (BLOCK_PX + LABEL_H)

    for row in range(LEDS):
        for col in range(LEDS):
            x0 = ox + col * CELL + DOT_MARGIN
            y0 = oy + row * CELL + DOT_MARGIN
            x1 = ox + col * CELL + CELL - DOT_MARGIN
            y1 = oy + row * CELL + CELL - DOT_MARGIN
            draw.ellipse([x0, y0, x1, y1], fill=colour)

    # Label centred below the block
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    tx = ox + (BLOCK_PX - tw) // 2
    ty = oy + BLOCK_PX + 2
    draw.text((tx, ty), label, fill=(180, 180, 180), font=font)


def main():
    img = Image.new("RGB", (TOTAL_W, TOTAL_H), BG)
    draw = ImageDraw.Draw(img)

    for i, (colour, label) in enumerate(COLOURS):
        bx = i % BLOCKS
        by = i // BLOCKS
        draw_block(draw, bx, by, colour, label)

    out = "green_test_preview.png"
    img.save(out)
    print(f"Saved {out}  ({TOTAL_W}×{TOTAL_H} px)")


if __name__ == "__main__":
    main()
