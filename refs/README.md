# Reference portraits

The generator sends real portraits with every request. That is what carries the
clay style, the lighting and the ring vignette, rather than a longer written
description of them.

The three portraits here are committed, so a clone works straight away with
nothing to download. They are derivative works, cropped from the starter bees in
block/buzz. See LICENSE in this directory for the attribution, the statement of
changes and the trademark note.

## Checking the provenance yourself

    ./refs/fetch.sh

That downloads the unmodified originals from block/buzz into `originals/` and
regenerates the crops with `make_references.py`. If the committed files are what
they claim to be, nothing changes. Continuous integration runs this on every
change for exactly that reason. It needs Pillow.

## Using your own portraits instead

Any square PNG in this directory is picked up. The generator prefers
fizz.png, honey.png and bumble.png when they exist, and otherwise uses every
PNG in the directory in sorted order.

To point at a different directory entirely, set BEE_REFS:

    export BEE_REFS=/path/to/your/portraits

Or pass paths on the command line:

    python3 bin/generate_bee.py --seed 7 --refs a.png b.png --out portrait.png

The style you get back is the style you send in. If you supply portraits in a
different style, the component library still works, but the output will follow
your references and not the clay bees.

Sharper references are better. The originals are 160 pixels wide and get scaled
up to 384, which is soft, and a soft reference gives the model less to copy. If
you already have crisp bust portraits, use those.
