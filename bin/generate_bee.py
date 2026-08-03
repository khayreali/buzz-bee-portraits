#!/usr/bin/env python3
"""Render a bee portrait through the Gemini image API.

The reference portraits are sent with every request, so the clay style, the
lighting and the vignette come from real examples rather than from adjectives.

Usage:
  ./generate_bee.py --seed 7 --out bee.png
  ./generate_bee.py --base-colour cobalt --antennae coil --out bee.png
  ./generate_bee.py --seed 7 --dry-run --out /dev/null

Needs GEMINI_API_KEY in the environment and at least one reference portrait in
the refs directory. The install ships three, so this normally just works.
"""

import argparse
import base64
import json
import os
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

import assemble_bee

HERE = Path(__file__).parent
DEFAULT_REFERENCE_DIRECTORY = HERE.parent / "refs"
PREFERRED_REFERENCES = ["fizz.png", "honey.png", "bumble.png"]
DEFAULT_MODEL = "gemini-3-pro-image"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
OUTPUT_SIZE = 384


def reference_directory():
    from_environment = os.environ.get("BEE_REFS")
    if from_environment:
        return Path(from_environment)
    return DEFAULT_REFERENCE_DIRECTORY


def find_references(override):
    if override:
        paths = []
        for item in override:
            paths.append(Path(item))
        return paths

    directory = reference_directory()
    paths = []
    for name in PREFERRED_REFERENCES:
        candidate = directory / name
        if candidate.exists():
            paths.append(candidate)

    if not paths:
        for candidate in sorted(directory.glob("*.png")):
            paths.append(candidate)

    return paths


def encode_references(paths):
    parts = []
    for path in paths:
        if not path.exists():
            sys.exit("reference portrait missing: " + str(path))
        encoded = base64.b64encode(path.read_bytes()).decode()
        parts.append({"inlineData": {"mimeType": "image/png", "data": encoded}})
    return parts


def build_request(prompt, reference_paths, size, seed):
    generation_config = {
        "responseModalities": ["IMAGE"],
        "imageConfig": {"aspectRatio": "1:1", "imageSize": size},
    }
    if seed is not None:
        generation_config["seed"] = seed

    parts = encode_references(reference_paths)
    parts.append({"text": prompt})

    return {
        "contents": [{"parts": parts}],
        "generationConfig": generation_config,
    }


def generate(prompt, reference_paths, api_key, model, size, seed, timeout=300):
    body = build_request(prompt, reference_paths, size, seed)
    request = urllib.request.Request(
        ENDPOINT.format(model),
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as error:
        sys.exit("HTTP " + str(error.code) + ": " + error.read().decode()[:800])

    candidates = payload.get("candidates")
    if not candidates:
        sys.exit("no candidates returned: " + json.dumps(payload)[:800])

    first = candidates[0]
    content = first.get("content")
    if content:
        parts = content.get("parts")
        if parts:
            for part in parts:
                if "inlineData" in part:
                    return base64.b64decode(part["inlineData"]["data"])

    reason = first.get("finishReason", "unknown")
    sys.exit("no image returned, finishReason=" + str(reason))


def resize_and_clean(path, size):
    """Downsample to the portrait size and drop the file metadata.

    Pillow is optional. Without it you keep the model's own resolution, which
    still works as an avatar, so this returns a message instead of failing.
    """
    try:
        from PIL import Image
    except ImportError:
        return "Pillow is not installed, so the image was left at full size"

    image = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    cleaned = Image.frombytes("RGB", image.size, image.tobytes())
    cleaned.save(path)
    return "resized to " + str(size) + " pixels"


def write_sidecar(output_path, arguments, model, picked, prompt):
    slots = {}
    for slot in assemble_bee.SLOT_ORDER:
        if picked.get(slot):
            slots[slot] = picked[slot]["id"]

    record = {
        "output": output_path.name,
        "seed": arguments.seed,
        "respect_taken": arguments.respect_taken,
        "model": model,
        "size": arguments.size,
        "slots": slots,
        "prompt": prompt,
    }

    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(json.dumps(record, indent=1) + "\n")
    return sidecar


def build_parser():
    parser = argparse.ArgumentParser(description="Generate a bee portrait.")
    parser.add_argument("-o", "--out", required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--prompt-file", help="use this prompt instead of the library")
    parser.add_argument("--size", default="1K", choices=["1K", "2K", "4K"])
    parser.add_argument("--refs", nargs="*", help="reference portraits to send")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt only")
    parser.add_argument("--keep-full", action="store_true", help="skip the resize")
    parser.add_argument("--respect-taken", action="store_true")
    assemble_bee.add_slot_arguments(parser)
    return parser


def main():
    parser = build_parser()
    arguments = parser.parse_args()

    picked = {}
    if arguments.prompt_file:
        prompt = Path(arguments.prompt_file).read_text()
    else:
        library = assemble_bee.load_library()
        choices = assemble_bee.collect_choices(arguments)
        generator = random.Random(arguments.seed)
        picked, prompt = assemble_bee.assemble(
            library, choices, generator, arguments.respect_taken
        )
        print(assemble_bee.describe(picked))

    print(prompt)
    if arguments.dry_run:
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit(
            "GEMINI_API_KEY is not set.\n"
            "  Buzz Desktop: Settings, Agents, Agent defaults, Advanced, "
            "Environment variables\n"
            "  Plain shell:  export GEMINI_API_KEY=your-key-here\n"
            "  Get a key at https://aistudio.google.com/apikey"
        )

    reference_paths = find_references(arguments.refs)
    if not reference_paths:
        sys.exit(
            "no reference portraits found in "
            + str(reference_directory())
            + "\n  Point BEE_REFS at a directory of square PNG portraits,"
            + "\n  or pass them with --refs."
        )

    model = os.environ.get("BEE_MODEL", DEFAULT_MODEL)
    image_bytes = generate(
        prompt, reference_paths, api_key, model, arguments.size, arguments.seed
    )

    output_path = Path(arguments.out)
    output_path.write_bytes(image_bytes)
    print()
    print("wrote " + str(output_path) + ", " + str(len(image_bytes)) + " bytes")

    if not arguments.keep_full:
        print(resize_and_clean(output_path, OUTPUT_SIZE))

    if picked:
        sidecar = write_sidecar(output_path, arguments, model, picked, prompt)
        print("wrote " + sidecar.name)


if __name__ == "__main__":
    main()
