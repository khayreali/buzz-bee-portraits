"""Generate one slot's worth of clay parts onto the blank base."""
import json, subprocess, sys, pathlib, concurrent.futures as futures
from PIL import Image, ImageDraw
import assemble as A

# Everything resolves from this file, so the tools work from a checkout,
# from an install, and from any working directory.
HERE = pathlib.Path(__file__).resolve().parent
SPRITES = HERE.parent
ROOT = SPRITES.parent

GEN = str(ROOT / "bin" / "generate_bee.py")
LIB = json.loads((ROOT / "bin" / "components.json").read_text())
BASE = str(SPRITES / "base.png")
WORKERS = 1
RETRIES = 12

TEMPLATE = """The attached image is a blank clay bee body. Reproduce this exact image, pixel for pixel identical in every respect, with one single change: add {what}.

Everything else must stay exactly as it is. The same grey clay, the same head shape and size, the same wings in the same positions, the same flat pure white background with no shadow on it, the same soft lighting from the upper left, the same framing and scale.

Do not add any other feature. The bee has no eyes, no nose, no mouth, no antennae, no hat, no glasses and no clothing except the one thing described here.

{desc} It is made of {material}, lit from the upper left in the same way as the body, and it casts a small soft contact shadow onto the clay where it meets the body.

Keep everything well inside a circle touching the four sides of the frame. Do not cast any shadow onto the white background.
"""

# what the slot is, and whether it is the same clay as the body
SLOTS = {
    "antennae": ("a pair of antennae on top of its head", True),
    "eyes":     ("a pair of eyes on the front of the head", False),
    "nose":     ("a nose in the middle of the face", True),
    "mouth":    ("a mouth on the lower half of the face", True),
    "headwear": ("a piece of headwear on top of its head", False),
    "glasses":  ("a pair of glasses on its face", False),
    "chest":    ("clothing or markings across its lower chest", False),
}

BODY_CLAY = "the same neutral light warm grey clay as the body"
OWN_CLAY = "clay in its own natural colours"

# Only one of the eye phrases in the library names a colour, because the
# library was written for whole-bee prompts where the house style carried
# that convention. Lifting the phrases into isolated part prompts dropped
# it, and the model invented a different palette every time, so half the
# eyes came out too dark to read against a coloured body. State it here.
MATERIALS = {
    "eyes": ("clay, with bright cream almost white clay for the whites of the eyes "
             "and clearly much darker grey brown clay for the pupils, a strong "
             "contrast between the two so the eyes read clearly at small size"),
}


def entries(slot, count):
    """Spread the picks across the list rather than taking the first N."""
    items = [e for e in LIB[slot] if isinstance(e, dict)]
    step = max(1, len(items) // count)
    return [items[i * step] for i in range(count)]


def prompt_for(slot, entry, tip=None):
    what, body_coloured = SLOTS[slot]
    desc = entry["phrase"]
    if tip:
        desc = f"The antennae are {desc}, {tip['phrase']}."
    else:
        desc = f"The {slot.rstrip('s') if slot != 'glasses' else 'glasses'} is {desc}." \
            if slot in ("nose", "mouth") else f"They are {desc}."
    material = MATERIALS.get(slot, BODY_CLAY if body_coloured else OWN_CLAY)
    return TEMPLATE.format(what=what, desc=desc, material=material)


def generate(slot, ident, text, seed):
    out = SPRITES / "parts" / slot / f"{ident}.png"
    if out.exists():
        return ident, True
    p = SPRITES / "parts" / slot / f"{ident}.txt"
    p.write_text(text)
    # The image API rate limits well below what four workers ask of it, and
    # it recovers within seconds, so back off and try again rather than
    # dropping the part.
    import time
    for attempt in range(RETRIES):
        subprocess.run([sys.executable, GEN, "--prompt-file", str(p), "--refs", BASE,
                        "--seed", str(seed + attempt * 97), "--out", str(out)],
                       capture_output=True, text=True)
        if out.exists():
            return ident, True
        # Tier 1 allows 10 dollars per rolling 10 minutes. Sleep long
        # enough for that window to move rather than hammering it.
        time.sleep(90)
    return ident, False


def run(slot, count=24):
    pathlib.Path(SPRITES / "parts" / slot).mkdir(parents=True, exist_ok=True)
    picks = entries(slot, count)
    jobs = []
    if slot == "antennae":
        tips = entries("antenna_tip", count)
        for i, (e, t) in enumerate(zip(picks, tips)):
            jobs.append((f"{e['id']}--{t['id']}", prompt_for(slot, e, t), 1000 + i))
    else:
        for i, e in enumerate(picks):
            jobs.append((e["id"], prompt_for(slot, e), 1000 + i))

    done = []
    with futures.ThreadPoolExecutor(WORKERS) as pool:
        futs = [pool.submit(generate, slot, i, t, s) for i, t, s in jobs]
        for f in futures.as_completed(futs):
            ident, ok = f.result()
            done.append((ident, ok))
            print(("  ok  " if ok else "  FAIL") + f" {ident}", flush=True)
    return [d for d, ok in done if ok]


def sheet(slot, cols=6):
    base = Image.open(BASE).convert("RGB")
    clay = A.paper_mask(base)
    files = sorted((SPRITES / "parts" / slot).glob("*.png"))
    if not files:
        print(f"no parts for {slot}, nothing to draw")
        return
    W = 200
    rows = (len(files) + cols - 1) // cols
    out = Image.new("RGB", (cols * W, rows * (W + 18)), "white")
    d = ImageDraw.Draw(out)
    for i, f in enumerate(files):
        layer = A.extract(base, str(f))
        canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
        body = base.convert("RGBA"); body.putalpha(clay)
        canvas.alpha_composite(body)
        canvas.alpha_composite(layer)
        thumb = canvas.convert("RGB").resize((W, W), Image.LANCZOS)
        x, y = (i % cols) * W, (i // cols) * (W + 18)
        out.paste(thumb, (x, y))
        d.text((x + 3, y + W + 3), f.stem[:30], fill=(60, 60, 60))
    out.save(f"sheet_{slot}.png")
    print("wrote", f"sheet_{slot}.png", out.size)


if __name__ == "__main__":
    slot = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    run(slot, n)
    sheet(slot)


def check(slot):
    """Reject parts where the model redrew the body instead of adding to it."""
    from PIL import ImageChops
    base = Image.open(BASE).convert("RGB")
    bb = A.paper_mask(base).load()
    w, h = base.size
    total = sum(1 for y in range(h) for x in range(w) if bb[x, y])
    low_band = int(h * 0.45) if slot in ("antennae", "headwear") else h
    bad = []
    for f in sorted((SPRITES / "parts" / slot).glob("*.png")):
        img = Image.open(f).convert("RGB")
        if img.size != base.size:
            img = img.resize(base.size)
        mp = A.paper_mask(img).load()
        lost = sum(1 for y in range(h) for x in range(w) if bb[x, y] and not mp[x, y])
        d = ImageChops.difference(base, img).convert("L").load()
        low = sum(1 for y in range(low_band, h) for x in range(w) if d[x, y] > 40)
        if lost > total * 0.02 or low > 800:
            bad.append(f.stem)
    return bad
