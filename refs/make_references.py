#!/usr/bin/env python3
"""Turn the downloaded portraits into the bust crops the generator sends.

The files in block/buzz are full standing figures on a transparent background.
The portraits this project makes are bust crops on white. If you send the full
figures as references the model follows their composition instead of the
prompt, and you get standing figures with the headwear slipped down onto the
chest. So we crop first.

The crop is a square anchored at the top of the visible content, a little wider
than the figure, which lands on the head filling the frame with the wings
spreading into the lower half. That is the composition the prompt describes.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
ORIGINALS = HERE / "originals"
OUTPUT_SIZE = 384

# Fraction of the figure width used as the square side, and how far above the
# top of the figure to start. Found by eye against the three starter bees. The
# margin matters: without headroom above the antennae the model puts headwear
# on the chest instead of the head.
WIDTH_SCALE = 0.90
TOP_MARGIN = 0.16


def crop_one(source, destination):
    from PIL import Image

    image = Image.open(source).convert("RGBA")
    box = image.getbbox()
    if box is None:
        sys.exit("image is completely transparent: " + str(source))

    left, top, right, bottom = box
    side = int((right - left) * WIDTH_SCALE)
    centre = (left + right) // 2
    start_x = centre - side // 2
    start_y = top - int(side * TOP_MARGIN)

    cropped = image.crop((start_x, start_y, start_x + side, start_y + side))

    white = Image.new("RGBA", cropped.size, (255, 255, 255, 255))
    white.alpha_composite(cropped)

    # No ring vignette here on purpose. The prompt asks for one and the model
    # draws it correctly. Drawing it into the reference instead makes the model
    # read it as a physical object and sculpt it out of clay.
    flat = white.convert("RGB").resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
    flat.save(destination)


def main():
    if not ORIGINALS.is_dir():
        sys.exit("no " + str(ORIGINALS) + ". Run ./refs/fetch.sh first.")

    sources = sorted(ORIGINALS.glob("*.png"))
    if not sources:
        sys.exit("no png files in " + str(ORIGINALS))

    for source in sources:
        destination = HERE / source.name
        crop_one(source, destination)
        print("wrote " + destination.name)


if __name__ == "__main__":
    main()
