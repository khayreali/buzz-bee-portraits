"""Render bees the way Buzz actually shows them, as circles."""
import random, pathlib
from PIL import Image, ImageDraw
import assemble as A, batch, mix

BASE = "base_noshadow.png"


def circle(im, size):
    im = im.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    out = Image.new("RGB", (size, size), "white")
    out.paste(im, (0, 0), mask)
    return out


def build(colour, chosen, base, clay):
    canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
    body = base.convert("RGBA")
    body.putalpha(clay)
    canvas.alpha_composite(A.tint(body, colour))
    for slot, body_coloured in mix.STACK:
        p = chosen.get(slot)
        if not p:
            continue
        layer = A.extract(base, str(p))
        canvas.alpha_composite(A.tint(layer, colour) if body_coloured else layer)
    return canvas.convert("RGB")


def catalogue():
    return {s: mix.usable(s) for s, _ in mix.STACK}


def roll(rng, cat, with_chest):
    chosen = {}
    for slot, _ in mix.STACK:
        opts = cat.get(slot)
        if not opts:
            continue
        if slot == "chest" and not with_chest:
            continue
        if slot in ("glasses", "headwear") and rng.random() > 0.35:
            continue
        chosen[slot] = rng.choice(opts)
    return chosen
