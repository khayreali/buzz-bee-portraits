#!/usr/bin/env python3
"""Build a bee portrait prompt from the component library.

Usage:
  ./assemble_bee.py --seed 7
  ./assemble_bee.py --base-colour cobalt --antennae coil --antenna-tip lamp
  ./assemble_bee.py --list eyes
"""

import argparse
import json
import random
import sys
from pathlib import Path

LIBRARY_PATH = Path(__file__).parent / "components.json"

# Accessories stay rare on purpose. If every bee has a hat, the hat identifies nobody.
RARITY = {"headwear": 1.0 / 6.0, "glasses": 1.0 / 6.0}

SLOT_ORDER = [
    "base_colour",
    "antennae",
    "antenna_tip",
    "eyes",
    "nose",
    "mouth",
    "chest",
    "headwear",
    "glasses",
]

TEMPLATE = """A claymation / plasticine character portrait of a cute stylised bee, in exactly \
the same handmade stop-motion clay style as the reference images: matte \
polymer-clay surface with subtle thumbprint texture, soft even studio lighting, \
gentle drop shadow, pure white background, square 1:1 crop, bust composition with \
a rounded cube head filling most of the frame and cropped by the bottom edge, two \
soft wings behind the head spreading into the lower half. Keep every part of the \
bee, including the tips of the antennae and the outer edge of the wings, well \
inside a circle touching the four sides of the frame, because the picture is \
displayed as a circle and the corners are cut away.

The bee is {base_colour}.

Its antennae are {antennae}, {antenna_tip}.

{face}

{chest}
{extras}
Charming handmade toy quality. No text, no letters, no logos."""


def load_library():
    return json.loads(LIBRARY_PATH.read_text())


def find_by_identifier(options, wanted):
    for option in options:
        if option["id"] == wanted:
            return option
    return None


def choose(library, slot, wanted, generator, respect_taken):
    options = library.get(slot, [])
    if not options:
        return None

    if wanted:
        found = find_by_identifier(options, wanted)
        if found is None:
            available = []
            for option in options:
                available.append(option["id"])
            sys.exit("no '" + wanted + "' in " + slot + ". options: " + ", ".join(available))
        return found

    if respect_taken:
        free = []
        for option in options:
            if not option.get("taken_by"):
                free.append(option)
        if free:
            options = free

    if slot in RARITY and generator.random() > RARITY[slot]:
        none_option = find_by_identifier(options, "none")
        if none_option is not None:
            return none_option

    return generator.choice(options)


def assemble(library, choices, generator, respect_taken=False):
    disabled = library.get("_disabled_slots", [])

    picked = {}
    for slot in SLOT_ORDER:
        wanted = choices.get(slot)
        if slot in disabled and not wanted:
            picked[slot] = None
        else:
            picked[slot] = choose(library, slot, wanted, generator, respect_taken)

    # Glasses cover the eyes. Describing both makes the model draw both.
    glasses = picked.get("glasses")
    if glasses and glasses.get("phrase"):
        lead = glasses["phrase"].replace("wearing ", "It wears ")
    else:
        lead = "It has " + picked["eyes"]["phrase"]

    face_parts = []
    for slot in ["nose", "mouth"]:
        option = picked.get(slot)
        if option and option.get("phrase"):
            face_parts.append(option["phrase"])

    face = lead
    if face_parts:
        face = face + ", " + ", ".join(face_parts)
    face = face + "."

    chest = ""
    if picked.get("chest"):
        chest = "Across the lower chest, " + picked["chest"]["phrase"] + "."

    # Anchor the headwear to the head. Without this the model puts anything that
    # is not obviously a hat, a pea pod or a cheese wedge, down on the chest.
    extras = ""
    headwear = picked.get("headwear")
    if headwear and headwear.get("phrase"):
        extras = "\nOn top of its head it is " + headwear["phrase"] + ".\n"

    prompt = TEMPLATE.format(
        base_colour=picked["base_colour"]["phrase"],
        antennae=picked["antennae"]["phrase"],
        antenna_tip=picked["antenna_tip"]["phrase"],
        face=face,
        chest=chest,
        extras=extras,
    )

    lines = []
    for line in prompt.splitlines():
        if line.strip() or line == "":
            lines.append(line)

    return picked, "\n".join(lines)


def describe(picked):
    parts = []
    for slot in SLOT_ORDER:
        if picked.get(slot):
            parts.append(slot + "=" + picked[slot]["id"])
    return "# " + "  ".join(parts)


def build_parser():
    parser = argparse.ArgumentParser(description="Build a bee portrait prompt.")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--list", metavar="SLOT", help="print every option in one slot")
    parser.add_argument(
        "--respect-taken",
        action="store_true",
        help="skip components already claimed by a bee on your roster",
    )
    add_slot_arguments(parser)
    return parser


def add_slot_arguments(parser):
    parser.add_argument("--base-colour", dest="base_colour")
    parser.add_argument("--antennae", dest="antennae")
    parser.add_argument("--antenna-tip", dest="antenna_tip")
    parser.add_argument("--eyes", dest="eyes")
    parser.add_argument("--nose", dest="nose")
    parser.add_argument("--mouth", dest="mouth")
    parser.add_argument("--chest", dest="chest")
    parser.add_argument("--headwear", dest="headwear")
    parser.add_argument("--glasses", dest="glasses")


def collect_choices(arguments):
    choices = {}
    choices["base_colour"] = arguments.base_colour
    choices["antennae"] = arguments.antennae
    choices["antenna_tip"] = arguments.antenna_tip
    choices["eyes"] = arguments.eyes
    choices["nose"] = arguments.nose
    choices["mouth"] = arguments.mouth
    choices["chest"] = arguments.chest
    choices["headwear"] = arguments.headwear
    choices["glasses"] = arguments.glasses
    return choices


def main():
    parser = build_parser()
    arguments = parser.parse_args()
    library = load_library()

    if arguments.list:
        if arguments.list not in SLOT_ORDER:
            sys.exit(
                "no slot called '" + arguments.list + "'. slots: "
                + ", ".join(SLOT_ORDER)
            )
        for option in library[arguments.list]:
            owner = ""
            if option.get("taken_by"):
                owner = "   [taken by " + option["taken_by"] + "]"
            print("  " + option["id"].ljust(16) + option.get("phrase", "")[:60] + owner)
        return

    choices = collect_choices(arguments)

    generator = random.Random(arguments.seed)
    picked, prompt = assemble(library, choices, generator, arguments.respect_taken)

    print(describe(picked))
    print()
    print(prompt)


if __name__ == "__main__":
    main()
