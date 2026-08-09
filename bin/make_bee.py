#!/usr/bin/env python3
"""Make a clay bee portrait from the shipped parts.

No network, no API key, no cost. The same seed always gives the same bee.
"""
import argparse
import json
import pathlib
import random
import sys

from PIL import Image

import parts as parts_module

HERE = pathlib.Path(__file__).resolve().parent
SPRITES = HERE.parent / "sprites"

# The order parts stack in. Later ones sit on top.
ORDER = ["antennae", "nose", "mouth", "eyes", "glasses", "headwear"]

# An accessory on every bee is noise, so they stay rare.
ACCESSORY_CHANCE = 0.35

COLOURS = {
    "amber": (217, 162, 27),
    "teal": (31, 122, 120),
    "dusty-pink": (191, 110, 116),
    "cobalt": (52, 86, 178),
    "moss": (108, 138, 62),
    "plum": (126, 74, 138),
    "rust": (176, 88, 48),
    "slate": (78, 96, 116),
    "mustard": (198, 158, 48),
    "clay-red": (168, 72, 62),
    "sea-green": (58, 134, 110),
    "lavender": (140, 128, 190),
}


def load_manifest():
    path = SPRITES / "manifest.json"
    if not path.exists():
        sys.exit(f"no manifest at {path}. Is the sprites directory installed?")
    return json.loads(path.read_text())


def choose(manifest, rng, overrides):
    chosen = {}
    recipe = {}
    for slot in ORDER:
        spec = manifest["slots"].get(slot)
        if spec is None:
            continue
        wanted = overrides.get(slot)
        if wanted == "none":
            continue
        if wanted is None:
            if spec["optional"] and rng.random() > ACCESSORY_CHANCE:
                continue
            wanted = rng.choice(spec["parts"])
        elif wanted not in spec["parts"]:
            sys.exit(
                f"no {slot} called {wanted}. Try --list {slot} to see them all."
            )
        chosen[slot] = SPRITES / "parts" / slot / f"{wanted}.png"
        recipe[slot] = wanted
    return chosen, recipe


def main():
    manifest = load_manifest()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--out", help="where to write the portrait")
    parser.add_argument("--seed", type=int, help="same seed, same bee")
    parser.add_argument("--colour", help="a name from --list colour, or a hex value")
    parser.add_argument("--size", type=int, default=384, help="output size in pixels")
    parser.add_argument("--list", metavar="SLOT", help="show what a slot holds")
    for slot in ORDER:
        parser.add_argument(f"--{slot}", help=f"pick a {slot} by name, or none")
    arguments = parser.parse_args()

    if arguments.list:
        if arguments.list in ("colour", "colours"):
            for name in sorted(COLOURS):
                print(name)
            return
        spec = manifest["slots"].get(arguments.list)
        if spec is None:
            sys.exit(f"no slot called {arguments.list}. Slots are: {', '.join(ORDER)}")
        for name in spec["parts"]:
            print(name)
        return

    if not arguments.out:
        parser.error("--out is required")

    seed = arguments.seed if arguments.seed is not None else random.randrange(1 << 30)
    rng = random.Random(seed)

    if arguments.colour:
        if arguments.colour in COLOURS:
            colour_name = arguments.colour
            colour = COLOURS[colour_name]
        else:
            text = arguments.colour.lstrip("#")
            if len(text) != 6:
                sys.exit(f"{arguments.colour} is not a colour name or a hex value")
            colour_name = "#" + text
            colour = tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    else:
        colour_name = rng.choice(sorted(COLOURS))
        colour = COLOURS[colour_name]

    overrides = {}
    for slot in ORDER:
        value = getattr(arguments, slot.replace("-", "_"), None)
        if value:
            overrides[slot] = value

    chosen, recipe = choose(manifest, rng, overrides)

    base = Image.open(SPRITES / manifest["base"]).convert("RGB")
    mask = parts_module.clay_mask(base)
    slots = {slot: manifest["slots"][slot]["body_coloured"] for slot in chosen}
    bee = parts_module.build(base, mask, colour, chosen, slots)

    if arguments.size != bee.size[0]:
        bee = bee.resize((arguments.size, arguments.size), Image.LANCZOS)

    out = pathlib.Path(arguments.out)
    bee.save(out)

    recipe["colour"] = colour_name
    recipe["seed"] = seed
    out.with_suffix(".json").write_text(json.dumps(recipe, indent=1) + "\n")

    print(f"wrote {out}")
    for slot in ORDER:
        if slot in recipe:
            print(f"  {slot:9} {recipe[slot]}")
    print(f"  {'colour':9} {colour_name}")
    print(f"  {'seed':9} {seed}")


if __name__ == "__main__":
    main()
