"""Assemble whole bees by mixing approved parts. No API calls, no key."""
import random, pathlib, json
from PIL import Image
import assemble as A
import batch

BASE = "base_noshadow.png"
# which slots recolour with the body, and the order they stack in
STACK = [("antennae", True), ("nose", True), ("mouth", True),
         ("chest", False), ("eyes", False), ("glasses", False), ("headwear", False)]

COLOURS = [
    ("amber",      (217, 162, 27)),  ("teal",   (31, 122, 120)),
    ("dusty-pink", (191, 110, 116)), ("cobalt", (52, 86, 178)),
    ("moss",       (108, 138, 62)),  ("plum",   (126, 74, 138)),
    ("rust",       (176, 88, 48)),   ("slate",  (78, 96, 116)),
]


def usable(slot):
    """Everything in a slot that passed the quality gate."""
    d = pathlib.Path(slot)
    if not d.exists():
        return []
    bad = set(batch.check(slot))
    return sorted(p for p in d.glob("*.png") if p.stem not in bad)


def make(rng, base, clay, catalogue):
    picked = {}
    name, colour = rng.choice(COLOURS)
    canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
    body = base.convert("RGBA")
    body.putalpha(clay)
    canvas.alpha_composite(A.tint(body, colour))
    for slot, body_coloured in STACK:
        options = catalogue.get(slot)
        if not options:
            continue
        # accessories stay rare, the way the library's own rules ask for
        if slot in ("glasses", "headwear") and rng.random() > 0.35:
            continue
        part = rng.choice(options)
        picked[slot] = part.stem
        layer = A.extract(base, str(part))
        canvas.alpha_composite(A.tint(layer, colour) if body_coloured else layer)
    picked["colour"] = name
    return canvas.convert("RGB"), picked


if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20260808
    base = Image.open(BASE).convert("RGB")
    clay = A.paper_mask(base)
    catalogue = {s: usable(s) for s, _ in STACK}
    for s, opts in catalogue.items():
        print(f"{s:10} {len(opts)} usable")
    rng = random.Random(seed)
    W = 300
    cols = 4
    rows = (count + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * W), "white")
    recipes = []
    for i in range(count):
        bee, picked = make(rng, base, clay, catalogue)
        sheet.paste(bee.resize((W, W), Image.LANCZOS), ((i % cols) * W, (i // cols) * W))
        recipes.append(picked)
    sheet.save("mix_sheet.png")
    print(json.dumps(recipes, indent=1)[:700])
