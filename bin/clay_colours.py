#!/usr/bin/env python3
"""Pick clay colours for new bees that do not collide with the ones you have.

Colour is the scarcest part of the system. At small sizes it does nearly all of
the work of telling one bee from another, so new colours are chosen by farthest
point packing inside CIELAB, with the colours you already use pinned in place.

Usage:
  ./clay_colours.py sample --count 12
  ./clay_colours.py sample --count 30 --json
  ./clay_colours.py check "#D9A21B"
  ./clay_colours.py measure refs
"""

import argparse
import json
import math
import sys
from pathlib import Path

# Colours that still read as plasticine. Widen these and you get more colours
# that look less like clay.
LIGHTNESS_RANGE = (35.0, 70.0)
CHROMA_RANGE = (25.0, 62.0)

COLLISION_THRESHOLD = 47.0

ROSTER_FILE = Path(__file__).parent / "roster.json"

HUE_ANCHORS = [
    (3.7, "dusty pink"),
    (18.8, "rose red"),
    (23.5, "crimson"),
    (35.5, "brick red"),
    (46.0, "terracotta"),
    (58.4, "rust orange"),
    (64.0, "burnt orange"),
    (82.1, "amber gold"),
    (87.4, "mustard yellow"),
    (101.0, "chartreuse"),
    (106.5, "olive green"),
    (138.4, "grass green"),
    (149.5, "leaf green"),
    (165.0, "jade green"),
    (180.1, "sea green"),
    (208.5, "deep teal"),
    (241.2, "petrol blue"),
    (258.2, "steel blue"),
    (281.0, "cobalt blue"),
    (289.8, "slate blue"),
    (299.4, "indigo"),
    (309.6, "violet"),
    (320.4, "purple"),
    (328.2, "magenta"),
    (335.0, "orchid"),
    (355.2, "raspberry"),
]


def load_roster():
    if not ROSTER_FILE.exists():
        return {}
    raw = json.loads(ROSTER_FILE.read_text())
    roster = {}
    for name in raw:
        values = raw[name]
        roster[name] = (values[0], values[1], values[2])
    return roster


def srgb_to_lab(red, green, blue):
    channels = []
    for value in [red, green, blue]:
        value = value / 255.0
        if value <= 0.04045:
            channels.append(value / 12.92)
        else:
            channels.append(((value + 0.055) / 1.055) ** 2.4)

    linear_red = channels[0]
    linear_green = channels[1]
    linear_blue = channels[2]

    x = (linear_red * 0.4124 + linear_green * 0.3576 + linear_blue * 0.1805) / 0.95047
    y = linear_red * 0.2126 + linear_green * 0.7152 + linear_blue * 0.0722
    z = (linear_red * 0.0193 + linear_green * 0.1192 + linear_blue * 0.9505) / 1.08883

    parts = []
    for value in [x, y, z]:
        if value > 0.008856:
            parts.append(value ** (1.0 / 3.0))
        else:
            parts.append(7.787 * value + 16.0 / 116.0)

    lightness = 116.0 * parts[1] - 16.0
    green_red = 500.0 * (parts[0] - parts[1])
    blue_yellow = 200.0 * (parts[1] - parts[2])
    return (lightness, green_red, blue_yellow)


def lab_to_srgb(colour):
    lightness = colour[0]
    green_red = colour[1]
    blue_yellow = colour[2]

    y_part = (lightness + 16.0) / 116.0
    x_part = y_part + green_red / 500.0
    z_part = y_part - blue_yellow / 200.0

    values = []
    for part in [x_part, y_part, z_part]:
        cubed = part ** 3
        if cubed > 0.008856:
            values.append(cubed)
        else:
            values.append((part - 16.0 / 116.0) / 7.787)

    x = values[0] * 0.95047
    y = values[1]
    z = values[2] * 1.08883

    linear_red = x * 3.2406 + y * -1.5372 + z * -0.4986
    linear_green = x * -0.9689 + y * 1.8758 + z * 0.0415
    linear_blue = x * 0.0557 + y * -0.2040 + z * 1.0570

    output = []
    for value in [linear_red, linear_green, linear_blue]:
        if value <= 0.0031308:
            value = 12.92 * value
        else:
            value = 1.055 * (value ** (1.0 / 2.4)) - 0.055
        output.append(value * 255.0)

    return output


def inside_srgb(colour):
    for value in lab_to_srgb(colour):
        if value < -0.5 or value > 255.5:
            return False
    return True


def to_hex(colour):
    parts = []
    for value in lab_to_srgb(colour):
        value = int(round(value))
        if value < 0:
            value = 0
        if value > 255:
            value = 255
        parts.append("%02X" % value)
    return "#" + "".join(parts)


def distance(first, second):
    total = 0.0
    for index in range(3):
        difference = first[index] - second[index]
        total = total + difference * difference
    return math.sqrt(total)


def to_lightness_chroma_hue(colour):
    lightness = colour[0]
    chroma = math.hypot(colour[1], colour[2])
    hue = math.degrees(math.atan2(colour[2], colour[1])) % 360.0
    return (lightness, chroma, hue)


def name_colour(colour):
    lightness, chroma, hue = to_lightness_chroma_hue(colour)

    best_name = HUE_ANCHORS[0][1]
    best_gap = 360.0
    for anchor_hue, anchor_name in HUE_ANCHORS:
        # Hue is a circle, so 350 and 10 are 20 degrees apart, not 340.
        gap = abs(hue - anchor_hue)
        if gap > 180.0:
            gap = 360.0 - gap
        if gap < best_gap:
            best_gap = gap
            best_name = anchor_name

    prefix = ""
    if lightness < 45.0:
        prefix = "deep "
    elif lightness > 60.0:
        prefix = "pale "

    if chroma < 34.0:
        prefix = prefix + "muted "
    elif chroma > 53.0:
        prefix = prefix + "vivid "

    return (prefix + best_name).strip()


def make_identifier(colour, used):
    base = name_colour(colour).replace(" ", "-")
    identifier = base
    counter = 2
    while identifier in used:
        identifier = base + "-" + str(counter)
        counter = counter + 1
    used.add(identifier)
    return identifier


def build_candidates(step):
    candidates = []
    lightness = LIGHTNESS_RANGE[0]
    while lightness <= LIGHTNESS_RANGE[1]:
        green_red = -90.0
        while green_red <= 90.0:
            blue_yellow = -90.0
            while blue_yellow <= 95.0:
                chroma = math.hypot(green_red, blue_yellow)
                if CHROMA_RANGE[0] <= chroma <= CHROMA_RANGE[1]:
                    colour = (lightness, green_red, blue_yellow)
                    if inside_srgb(colour):
                        candidates.append(colour)
                blue_yellow = blue_yellow + step
            green_red = green_red + step
        lightness = lightness + step
    return candidates


def pack(count, pinned, step):
    candidates = build_candidates(step)
    if not candidates:
        sys.exit("no candidates inside the clay gamut, check the ranges")

    nearest = []
    for candidate in candidates:
        if pinned:
            shortest = distance(candidate, pinned[0])
            for existing in pinned:
                gap = distance(candidate, existing)
                if gap < shortest:
                    shortest = gap
            nearest.append(shortest)
        else:
            nearest.append(float("inf"))

    picked = []
    for _ in range(count):
        best_index = 0
        for index in range(len(candidates)):
            if nearest[index] > nearest[best_index]:
                best_index = index

        choice = candidates[best_index]
        picked.append(choice)

        for index in range(len(candidates)):
            gap = distance(candidates[index], choice)
            if gap < nearest[index]:
                nearest[index] = gap

    return picked


def lowest_separation(colours):
    if len(colours) < 2:
        return float("inf")
    lowest = None
    for first in range(len(colours)):
        for second in range(first + 1, len(colours)):
            gap = distance(colours[first], colours[second])
            if lowest is None or gap < lowest:
                lowest = gap
    return lowest


def nearest_roster_entry(colour, roster):
    best_name = None
    best_gap = None
    for name in roster:
        gap = distance(colour, roster[name])
        if best_gap is None or gap < best_gap:
            best_gap = gap
            best_name = name
    return best_name, best_gap


def command_sample(arguments):
    roster = load_roster()

    pinned = []
    for name in roster:
        pinned.append(roster[name])

    picked = pack(arguments.count, pinned, arguments.step)

    used = set()
    rows = []
    for colour in picked:
        nearest_name, nearest_gap = nearest_roster_entry(colour, roster)
        rows.append(
            {
                "id": make_identifier(colour, used),
                "phrase": name_colour(colour) + " clay",
                "hex": to_hex(colour),
                "nearest": nearest_name,
                "separation": nearest_gap,
            }
        )

    if arguments.json:
        output = []
        for row in rows:
            output.append(
                {
                    "id": row["id"],
                    "phrase": row["phrase"],
                    "hex": row["hex"],
                    "taken_by": None,
                }
            )
        print(json.dumps(output, indent=1))
    else:
        print("identifier".ljust(28) + "hex".ljust(10) + "separation  nearest")
        for row in rows:
            separation = "n/a"
            if row["separation"] is not None:
                separation = "%.1f" % row["separation"]
            nearest = row["nearest"] or "none"
            print(row["id"].ljust(28) + row["hex"].ljust(10) + separation.rjust(10) + "  " + nearest)

        everything = pinned + picked
        if pinned:
            print()
            print("existing roster floor  %.1f" % lowest_separation(pinned))
        print("floor including new    %.1f, over %d colours" % (lowest_separation(everything), len(everything)))

    if arguments.swatch:
        write_swatch(rows, arguments.swatch)
        print()
        print("wrote " + arguments.swatch)


def write_swatch(rows, path):
    from PIL import Image, ImageDraw

    columns = 8
    cell = 96
    row_count = (len(rows) + columns - 1) // columns

    image = Image.new("RGB", (columns * cell, row_count * (cell + 18)), "white")
    drawing = ImageDraw.Draw(image)

    for index in range(len(rows)):
        left = (index % columns) * cell
        top = (index // columns) * (cell + 18)
        drawing.rectangle(
            [left + 4, top + 4, left + cell - 4, top + cell - 4], fill=rows[index]["hex"]
        )
        drawing.text((left + 5, top + cell - 1), rows[index]["id"][:16], fill="black")

    image.save(path)


def command_check(arguments):
    roster = load_roster()

    text = arguments.hex.lstrip("#")
    red = int(text[0:2], 16)
    green = int(text[2:4], 16)
    blue = int(text[4:6], 16)

    colour = srgb_to_lab(red, green, blue)
    lightness, chroma, hue = to_lightness_chroma_hue(colour)

    print("%s  lightness %.1f chroma %.1f hue %.1f, reads as %s"
          % (arguments.hex, lightness, chroma, hue, name_colour(colour)))

    in_gamut = (
        LIGHTNESS_RANGE[0] <= lightness <= LIGHTNESS_RANGE[1]
        and CHROMA_RANGE[0] <= chroma <= CHROMA_RANGE[1]
    )
    if in_gamut:
        print("clay gamut: yes")
    else:
        print("clay gamut: no, outside lightness 35 to 70 or chroma 25 to 62")

    if not roster:
        print()
        print("no roster.json found, so there is nothing to compare against")
        return

    print()
    pairs = []
    for name in roster:
        pairs.append((distance(colour, roster[name]), name))
    pairs.sort()

    for gap, name in pairs:
        verdict = "ok"
        if gap < COLLISION_THRESHOLD:
            verdict = "collides"
        print("  " + name.ljust(10) + "%6.1f  %s" % (gap, verdict))

    print()
    print("Separation below %.0f is where two bees start to look alike at small sizes."
          % COLLISION_THRESHOLD)


def command_measure(arguments):
    from PIL import Image
    import colorsys

    directory = Path(arguments.directory)
    if not directory.exists():
        sys.exit("no such directory: " + str(directory))

    files = sorted(directory.glob("*.png"))
    if not files:
        sys.exit("no png files in " + str(directory))

    measured = {}
    for path in files:
        image = Image.open(path).convert("RGB")
        raw = image.tobytes()

        pixels = []
        position = 0
        while position < len(raw):
            red = raw[position]
            green = raw[position + 1]
            blue = raw[position + 2]
            pixels.append((red, green, blue))
            position = position + 3

        saturated = []
        for red, green, blue in pixels:
            _, level, saturation = colorsys.rgb_to_hls(red / 255.0, green / 255.0, blue / 255.0)
            if saturation > 0.25 and 0.15 < level < 0.85:
                saturated.append((red, green, blue))

        if not saturated:
            print(path.stem.ljust(10) + "no saturated pixels found")
            continue

        total_lightness = 0.0
        total_green_red = 0.0
        total_blue_yellow = 0.0
        for red, green, blue in saturated:
            values = srgb_to_lab(red, green, blue)
            total_lightness = total_lightness + values[0]
            total_green_red = total_green_red + values[1]
            total_blue_yellow = total_blue_yellow + values[2]

        count = len(saturated)
        average = (
            total_lightness / count,
            total_green_red / count,
            total_blue_yellow / count,
        )
        measured[path.stem] = average

        print(path.stem.ljust(10) + to_hex(average).ljust(10)
              + "lightness %5.1f  %s" % (average[0], name_colour(average)))

    if arguments.write:
        output = {}
        for name in measured:
            values = measured[name]
            output[name] = [round(values[0], 1), round(values[1], 1), round(values[2], 1)]
        ROSTER_FILE.write_text(json.dumps(output, indent=1) + "\n")
        print()
        print("wrote " + ROSTER_FILE.name)


def main():
    parser = argparse.ArgumentParser(description="Pick clay colours for new bees.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sample = subparsers.add_parser("sample", help="pack new colours away from your roster")
    sample.add_argument("--count", type=int, default=12)
    sample.add_argument("--step", type=float, default=4.0)
    sample.add_argument("--json", action="store_true")
    sample.add_argument("--swatch", metavar="PNG")
    sample.set_defaults(handler=command_sample)

    check = subparsers.add_parser("check", help="compare one colour against your roster")
    check.add_argument("hex")
    check.set_defaults(handler=command_check)

    measure = subparsers.add_parser("measure", help="read colours out of portrait files")
    measure.add_argument("directory", nargs="?", default=str(Path(__file__).parent.parent / "refs"))
    measure.add_argument("--write", action="store_true", help="save the result as roster.json")
    measure.set_defaults(handler=command_measure)

    arguments = parser.parse_args()
    arguments.handler(arguments)


if __name__ == "__main__":
    main()
