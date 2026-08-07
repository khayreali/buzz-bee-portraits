<div align="center">

# buzz-bee-portraits

**Claymation bee portraits for your Buzz agents, generated from a written component library.**

[![ci](https://github.com/khayreali/buzz-bee-portraits/actions/workflows/ci.yml/badge.svg)](https://github.com/khayreali/buzz-bee-portraits/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![model](https://img.shields.io/badge/model-Gemini%203%20Pro%20Image-8E75B2.svg)](https://aistudio.google.com/apikey)
[![skill](https://img.shields.io/badge/Buzz-Agent%20Skill-F5A623.svg)](https://github.com/block/buzz)

[Install](#install) · [API key](#the-api-key) · [Usage](#usage) · [Component library](#the-component-library) · [Colour tool](#the-colour-tool) · [Cost](#cost) · [Design notes](docs/BEE_PORTRAIT_SYSTEM.md)

![eight generated bees](docs/examples.png)

<sub>Eight portraits from eight random seeds. Nothing hand picked.</sub>

</div>

---

## Introduction

Every agent you create starts out wearing the same stock icon as every other agent.
This gives each one a face instead.

- **Written, not composited.** Nine slots hold English sentences, not sprites. The
  generator assembles them into one prompt, so the model sculpts a single coherent
  bee rather than pasting layers together.
- **Consistent with the set.** Three reference portraits ride along with every
  request, which is what holds the clay style steady across generations.
- **Reproducible.** The same seed always gives the same bee, and every image is
  written with a JSON sidecar recording the seed, model, size and every slot choice.
- **Roughly a hundred entries per slot.** Base colour, antennae, antenna tip, eyes,
  nose, mouth, chest, headwear and glasses. The combinations do not run out.
- **One dependency.** Python 3. Pillow is optional.

---

## Install

One command. Nothing to clone:

```bash
curl -fsSL https://raw.githubusercontent.com/khayreali/buzz-bee-portraits/main/install.sh | sh
```

If you already have a clone, run `./install.sh` from inside it instead.

The installer copies the skill, the scripts and the three reference portraits into
`~/.buzz/.agents/skills/bee-portrait/`, then links that directory into every agent
runtime set up in your nest, because each runtime only reads its own skill folder:

| Runtime | Reads from |
| --- | --- |
| Claude Code | `.claude/skills/` |
| Goose | `.goose/skills/` |
| Codex | `.codex/skills/` |

The skill is self contained, so you never have to keep a checkout around or tell
anything where one is. Restart your agent and `bee-portrait` appears in its skill list.

```bash
./install.sh --check          # report what is installed and what is linked
BUZZ_NEST=/path ./install.sh  # if your agents do not run in ~/.buzz
```

Python 3 is the only thing you need. Pillow is optional, and without it you get the
model's own resolution instead of a 384 pixel square. Everything else works the same.

---

## The API key

This is the one thing you have to do yourself. Get a Google Gemini API key from
https://aistudio.google.com/apikey.

In Buzz Desktop, add it under Settings, Agents, Agent defaults, Advanced, Environment
variables, with the name `GEMINI_API_KEY`. It is then handed to every agent session.
In a shell, `export GEMINI_API_KEY=your-key-here` does the same job.

---

## Usage

The examples below use `bin/` from a clone. If you installed rather than cloned, the
same scripts are in the skill directory, so set this once and every example works
unchanged:

```bash
cd ~/.buzz/.agents/skills/bee-portrait
```

### Assemble a prompt

This makes no network call and needs no key:

```bash
python3 bin/assemble_bee.py --seed 7
```

It prints the slots it chose, then the prompt, which ends like this:

```
On top of its head it is wearing an open pea pod tipped upside down with the peas showing.
```

The same seed always produces the same choices, so you can share a seed and get the
same bee back. To choose slots by hand, use the flag named after the slot, with
underscores written as hyphens. Anything you do not name is still filled at random:

```bash
python3 bin/assemble_bee.py --base-colour cobalt --antennae coil --antenna-tip lamp
```

See what a slot holds with `python3 bin/assemble_bee.py --list chest`. Passing an
identifier that does not exist also prints every identifier the slot does have.

### Generate the image

Run the first as often as you like, it only prints the prompt. The second costs money:

```bash
python3 bin/generate_bee.py --seed 7 --dry-run --out /dev/null
python3 bin/generate_bee.py --seed 7 --out mybee.png
```

`generate_bee.py` takes the same slot flags as the assembler, and `--out` is required.

| Flag | What it does |
| --- | --- |
| `--size` | `1K`, `2K` or `4K`. Default `1K` |
| `--dry-run` | Print the prompt, call nothing |
| `--keep-full` | Skip the downsample to 384 pixels |
| `--refs` | Use different reference portraits |
| `--prompt-file` | Use your own prompt text |
| `--respect-taken` | Filter out components claimed by another roster |

### Put it on an agent

```bash
buzz upload file --file mybee.png
buzz users set-profile --avatar <url>
```

`set-profile` only ever updates the identity that runs it, so an agent has to apply
its own portrait. Nobody can apply one on its behalf.

> **Buzz Desktop users, read this one.** Desktop stores an avatar on the agent record
> and re-publishes that record whenever an agent starts and the relay disagrees with
> it. A picture applied with `set-profile` alone changes the relay but not the record,
> so it can be replaced the next time that agent starts. To make a portrait stick, set
> it on the agent in Desktop as well.

---

## The component library

`bin/components.json` holds the nine slots. Most hold one hundred entries. They are
written sentences, not sprites, and nothing is composited. Each entry needs two fields:

```json
{"id": "coil", "phrase": "two tightly coiled spring antennae"}
```

The phrase goes into the prompt word for word, so write it the way you would describe
the thing to somebody sculpting it, not the way you would tag it. The `id` is what you
type after a flag such as `--antennae`.

To extend the library, add entries to the lists. There is no schema to update and no
registration step, and no list has a fixed length. The `_hard_rules` key in the same
file explains the conventions, including that headwear is decorative and never encodes
what an agent does, and that accessories stay rare, roughly one bee in six.

---

## The colour tool

`bin/clay_colours.py` picks base colours that stay visually separated from the bees you
already have, measured in CIELAB rather than by eye. Measure your existing portraits
first, because `--write` saves the result as `bin/roster.json`, which `check` and
`sample` both read:

```bash
python3 bin/clay_colours.py measure refs --write
python3 bin/clay_colours.py sample --count 5
python3 bin/clay_colours.py check '#D9A21B'
```

`sample` also takes `--json`, which prints entries shaped for `components.json`, and
`--swatch out.png`, which writes a labelled picture. Measuring and swatches use Pillow.

---

## Two things to know

**The `taken_by` fields name somebody else's roster.** Entries in `base_colour` and
`antenna_tip` are marked as claimed by Honey, Fizz, Bumble, Hive, Jelly, Comb and
Nectar, which are the original author's agents. `--respect-taken` filters out anything
carrying one, so on your machine it reserves components for bees that do not exist.
Leave the flag off, which is the default and is safe, or edit `components.json` to
carry your own names.

**The glasses slot is filled but switched off.** There are one hundred glasses entries
and the assembler never reaches them, because `_disabled_slots` contains `"glasses"`.
Remove it to turn the slot on. You can also pass `--glasses` with an identifier without
enabling the slot, since an explicit choice overrides the disabled list.

---

## What is in the repository

```
bin/                  the three scripts and components.json
refs/                 the reference portraits sent with every request
skills/bee-portrait/  the skill an agent loads, this is what install.sh copies
agents/               one persona, so the repository is a valid Buzz persona pack
.plugin/plugin.json   the pack manifest
tests/check_repo.py   the checks continuous integration runs
docs/                 the design reasoning
```

The skill is the part almost everybody wants, and `install.sh` installs exactly that.

The `agents/` and `.plugin/` directories make this a persona pack, which is the format
Buzz documents for shipping personas and skills together. Buzz can validate a pack
today with `buzz pack validate .`, but it has no command that installs one, and Desktop
import handles only agent and team snapshots. That is why `install.sh` exists. If an
install path lands, this repository is already the right shape.

---

## Cost

Every portrait is a paid call to Google.

| Size | Roughly |
| --- | --- |
| `1K` (default) | 13 to 14 cents |
| `4K` | 24 cents |
| `--dry-run` | free, calls nothing |

Nothing is cached, so a rejected image costs the same as a kept one, and you should
expect two or three tries before you like one.

Generation takes about thirteen seconds, effectively all of it waiting on the model.
The local work of choosing components and writing the prompt is a few hundredths of a
second, so there is nothing here worth optimising.

---

## Licensing and attribution

This repository is licensed under Apache-2.0. See `LICENSE` and `NOTICE`.

The three reference portraits in `refs/` are derivative works. They come from
https://github.com/block/buzz, Copyright 2026 Block, Inc., also Apache-2.0, cropped to
square busts on a white background and resized. `refs/LICENSE` carries the attribution
notice and the statement of changes, and `refs/fetch.sh` re-derives the files from the
untouched originals if you want to verify that provenance. You do not need to run it to
use this project.

Apache-2.0 section 6 grants no rights in trade names or trademarks, and a mascot is
exactly the sort of thing that functions as brand identity. So, plainly: this is not
Block branding, it is not endorsed by Block, and nothing here implies any relationship
with Block. Generate bees for your own roster, and do not adopt Fizz, Honey or Bumble
as your own identity. That is what the licence files say, and it is not legal advice.

---

## Further reading

[docs/BEE_PORTRAIT_SYSTEM.md](docs/BEE_PORTRAIT_SYSTEM.md) has the design reasoning:
why the system uses written descriptions instead of sprites, why the references go with
every request, and what survives at small sizes.
