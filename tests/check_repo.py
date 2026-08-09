#!/usr/bin/env python3
"""Check the repository is well formed before anyone clones it.

Runs three groups of checks:
  library  the component library is internally consistent
  pack     the persona pack layout matches what buzz pack validate requires
  smoke    the assembler produces a prompt for many seeds

This does not replace `buzz pack validate .`, which is the authoritative check
if you have the Buzz command line tool. It re-implements the parts of it that
matter so continuous integration can run without building Buzz from source.
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BIN = ROOT / "bin"

sys.path.insert(0, str(BIN))
import assemble_bee

MANIFEST_KEYS = [
    "$schema",
    "id",
    "name",
    "version",
    "description",
    "author",
    "license",
    "homepage",
    "repository",
    "keywords",
    "engines",
    "personas",
    "defaults",
    "pack_instructions",
    "hooks_config",
    "mcp_config",
]

NAME_CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"

problems = []
warnings = []


def fail(message):
    problems.append(message)


def warn(message):
    warnings.append(message)


def read_frontmatter(path):
    """Pull the top level key and value pairs out of a YAML frontmatter block."""
    text = path.read_text()
    if not text.startswith("---"):
        return None

    end = text.find("\n---", 3)
    if end == -1:
        return None

    block = text[3:end]
    fields = {}
    for line in block.splitlines():
        if not line or line.startswith("#") or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        fields[key.strip()] = value
    return fields


def check_library():
    library = assemble_bee.load_library()
    disabled = library.get("_disabled_slots", [])

    for slot in assemble_bee.SLOT_ORDER:
        entries = library.get(slot)
        if not entries:
            fail("slot " + slot + " is missing or empty")
            continue

        identifiers = set()
        phrases = set()
        for entry in entries:
            identifier = entry.get("id")
            phrase = entry.get("phrase")
            if not identifier:
                fail("slot " + slot + " has an entry with no id")
                continue
            if not phrase and identifier != "none":
                fail("slot " + slot + " entry " + identifier + " has no phrase")
            if identifier in identifiers:
                fail("slot " + slot + " has a duplicate id: " + identifier)
            identifiers.add(identifier)
            if phrase:
                if phrase in phrases:
                    fail("slot " + slot + " has a duplicate phrase: " + identifier)
                phrases.add(phrase)

        if slot in disabled:
            continue
        if len(entries) < 5:
            warn("slot " + slot + " only has " + str(len(entries)) + " entries")

    print("library: " + str(len(assemble_bee.SLOT_ORDER)) + " slots checked")


def check_manifest():
    path = ROOT / ".plugin" / "plugin.json"
    if not path.exists():
        fail("missing .plugin/plugin.json")
        return []

    try:
        manifest = json.loads(path.read_text())
    except ValueError as error:
        fail("plugin.json is not valid json: " + str(error))
        return []

    for field in ["id", "name", "version"]:
        value = manifest.get(field)
        if not value or not str(value).strip():
            fail("plugin.json is missing a non empty " + field)

    for key in manifest:
        if key not in MANIFEST_KEYS:
            warn("plugin.json has an unknown key: " + key)

    personas = manifest.get("personas", [])
    if not personas:
        fail("plugin.json lists zero personas, buzz pack validate hard fails on this")

    print("manifest: ok")
    return personas


def check_personas(listed):
    on_disk = sorted((ROOT / "agents").glob("*.persona.md"))
    if not on_disk:
        fail("no agents/*.persona.md files, a pack with zero personas fails validation")
        return

    for relative in listed:
        if not (ROOT / relative).exists():
            fail("plugin.json lists a persona that does not exist: " + relative)

    seen = set()
    for path in on_disk:
        fields = read_frontmatter(path)
        if fields is None:
            fail(path.name + " has no yaml frontmatter block")
            continue

        for field in ["name", "display_name", "description"]:
            if not fields.get(field):
                fail(path.name + " frontmatter is missing " + field)

        name = fields.get("name", "")
        if len(name) > 64:
            fail(path.name + " persona name is longer than 64 characters")
        for character in name:
            if character not in NAME_CHARACTERS:
                fail(path.name + " persona name has an illegal character: " + character)
                break
        if name in seen:
            fail("two personas share the name " + name)
        seen.add(name)

    print("personas: " + str(len(on_disk)) + " checked")


def check_skills():
    directory = ROOT / "skills"
    if not directory.exists():
        warn("no skills directory")
        return

    found = 0
    for child in sorted(directory.iterdir()):
        if not child.is_dir():
            continue
        path = child / "SKILL.md"
        if not path.exists():
            fail("skills/" + child.name + " has no SKILL.md")
            continue

        fields = read_frontmatter(path)
        if fields is None:
            fail(child.name + "/SKILL.md has no yaml frontmatter, it will be silently skipped")
            continue

        for field in ["name", "description"]:
            if not fields.get(field):
                fail(child.name + "/SKILL.md is missing " + field + ", it will be silently skipped")

        if fields.get("name") and fields["name"] != child.name:
            warn(child.name + "/SKILL.md name is " + fields["name"] + ", which does not match the directory")

        found = found + 1

    if found == 0:
        warn("no skills found")
    print("skills: " + str(found) + " checked")


def check_shipped_references():
    """A clone must work with no download, so the portraits have to be here."""
    directory = ROOT / "refs"
    portraits = sorted(directory.glob("*.png"))
    if not portraits:
        fail("no reference portraits committed in refs, a fresh clone cannot generate")
        return

    for name in ["fizz.png", "honey.png", "bumble.png"]:
        if not (directory / name).exists():
            fail("refs/" + name + " is missing")

    if not (directory / "LICENSE").exists():
        fail("refs/LICENSE is missing, the portraits are derivative works")

    print("references: " + str(len(portraits)) + " committed")


def check_documented_identifiers():
    """Every --slot identifier written in the docs has to exist in the library.

    A wrong identifier in a document is invisible until somebody types it and
    the tool exits, which is exactly how --glasses round-wire survived.
    """
    library = assemble_bee.load_library()

    flag_for_slot = {}
    identifiers_for_flag = {}
    for slot in assemble_bee.SLOT_ORDER:
        flag = "--" + slot.replace("_", "-")
        flag_for_slot[flag] = slot
        identifiers = []
        for entry in library.get(slot, []):
            identifiers.append(entry["id"])
        identifiers_for_flag[flag] = identifiers

    # The readme documents make_bee.py, whose parts come from the sprite
    # manifest rather than the phrase library. Both tools share flag names,
    # so an identifier is valid if either one accepts it. Checking only the
    # library reported the readme as broken when it was correct.
    manifest_path = ROOT / "sprites" / "manifest.json"
    if manifest_path.exists():
        sprite_manifest = json.loads(manifest_path.read_text())
        for slot, spec in sprite_manifest["slots"].items():
            flag = "--" + slot.replace("_", "-")
            flag_for_slot[flag] = slot
            identifiers_for_flag.setdefault(flag, [])
            identifiers_for_flag[flag] = identifiers_for_flag[flag] + spec["parts"]

    checked = 0
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue

        # Only look inside code, either a fenced block or a backtick span.
        # In prose people write "pass --glasses with an identifier", and the
        # word after the flag is not meant to be an identifier at all. Inside
        # backticks it always is.
        snippets = []
        inside_block = False
        for line in path.read_text(errors="ignore").splitlines():
            if line.strip().startswith("```"):
                inside_block = not inside_block
                continue
            if inside_block:
                snippets.append(line)
                continue
            pieces = line.split("`")
            index = 1
            while index < len(pieces):
                snippets.append(pieces[index])
                index = index + 2

        for snippet in snippets:
            words = snippet.split()
            position = 0
            while position < len(words) - 1:
                flag = words[position]
                value = words[position + 1].strip(".,;:)")
                position = position + 1

                if flag not in flag_for_slot:
                    continue
                if not value or value.startswith("-"):
                    continue

                checked = checked + 1
                if value not in identifiers_for_flag[flag]:
                    fail(
                        path.name + " documents " + flag + " " + value
                        + ", which is not in the " + flag_for_slot[flag] + " slot"
                    )

    print("documented identifiers: " + str(checked) + " checked")


def check_smoke():
    library = assemble_bee.load_library()
    empty = {}
    for slot in assemble_bee.SLOT_ORDER:
        empty[slot] = None

    for seed in range(50):
        generator = random.Random(seed)
        picked, prompt = assemble_bee.assemble(library, empty, generator, False)
        if len(prompt) < 200:
            fail("seed " + str(seed) + " produced a suspiciously short prompt")
        if "None" in prompt:
            fail("seed " + str(seed) + " left an unfilled slot in the prompt")

    print("smoke: 50 seeds assembled")


def check_no_em_dashes():
    suffixes = [".py", ".md", ".json", ".sh", ".yml"]
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if path.name == "check_repo.py":
            continue
        text = path.read_text(errors="ignore")
        if "—" in text:
            fail("em dash found in " + str(path.relative_to(ROOT)))

    print("style: em dash scan done")



def check_sprites():
    """The parts are the product, so a missing one is an error, not a warning.

    The manifest is what make_bee.py reads. If it names a part that is not on
    disk the tool crashes for whoever installed it, and if a part sits on disk
    unlisted it was either rejected by the quality gate or forgotten. Both are
    worth failing over.
    """
    sprites = ROOT / "sprites"
    manifest_path = sprites / "manifest.json"
    if not manifest_path.exists():
        fail("sprites/manifest.json is missing, so nothing can be assembled")
        return

    manifest = json.loads(manifest_path.read_text())

    base = sprites / manifest.get("base", "base.png")
    if not base.exists():
        fail("the base at " + str(base) + " is missing")

    listed = 0
    for slot, spec in manifest["slots"].items():
        directory = sprites / "parts" / slot
        if not directory.is_dir():
            fail("slot " + slot + " has no directory at " + str(directory))
            continue

        on_disk = set(path.stem for path in directory.glob("*.png"))
        for identifier in spec["parts"]:
            listed += 1
            if identifier not in on_disk:
                fail("manifest lists " + slot + "/" + identifier + " but the file is missing")

        # A part on disk that is neither shipped nor recorded as rejected has
        # been forgotten, and that is worth saying out loud.
        accounted = set(spec["parts"]) | set(spec.get("rejected", []))
        for identifier in sorted(on_disk - accounted):
            fail(slot + "/" + identifier + " is on disk but neither listed nor rejected")

        for identifier in spec.get("rejected", []):
            if identifier in spec["parts"]:
                fail(slot + "/" + identifier + " is both shipped and rejected")

        if not spec["parts"]:
            fail("slot " + slot + " has no usable parts")

    print("sprites: " + str(listed) + " parts listed and present")


def check_make_bee():
    """Actually build bees, because a manifest that parses proves nothing."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        first = Path(directory) / "one.png"
        again = Path(directory) / "two.png"

        result = subprocess.run(
            [sys.executable, str(BIN / "make_bee.py"), "--seed", "7", "--out", str(first)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            fail("make_bee.py failed: " + result.stderr.strip().splitlines()[-1])
            return

        subprocess.run(
            [sys.executable, str(BIN / "make_bee.py"), "--seed", "7", "--out", str(again)],
            capture_output=True, text=True,
        )
        if first.read_bytes() != again.read_bytes():
            fail("the same seed produced two different bees")

        if not first.with_suffix(".json").exists():
            fail("make_bee.py did not write the recipe beside the image")

        # A handful of seeds, so a part that breaks assembly shows up here
        # rather than in somebody else's terminal.
        for seed in (1, 2, 3, 4, 5):
            out = Path(directory) / ("s" + str(seed) + ".png")
            run = subprocess.run(
                [sys.executable, str(BIN / "make_bee.py"), "--seed", str(seed), "--out", str(out)],
                capture_output=True, text=True,
            )
            if run.returncode != 0 or not out.exists():
                fail("make_bee.py failed on seed " + str(seed))
                return

    print("make_bee: 7 bees built, same seed reproduces")


def main():
    check_library()
    check_sprites()
    check_make_bee()
    personas = check_manifest()
    check_personas(personas)
    check_skills()
    check_shipped_references()
    check_documented_identifiers()
    check_smoke()
    check_no_em_dashes()

    print()
    for message in warnings:
        print("warning: " + message)
    for message in problems:
        print("error: " + message)

    if problems:
        print()
        print(str(len(problems)) + " error(s), " + str(len(warnings)) + " warning(s)")
        return 1

    print()
    print("all checks passed, " + str(len(warnings)) + " warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
