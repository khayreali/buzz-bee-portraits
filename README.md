<div align="center">

# Buzz Claymation Portraits

**Claymation bee portraits for your Buzz agents.**

[![ci](https://github.com/khayreali/buzz-bee-portraits/actions/workflows/ci.yml/badge.svg)](https://github.com/khayreali/buzz-bee-portraits/actions/workflows/ci.yml)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![parts](https://img.shields.io/badge/parts-111-F5A623.svg)](#the-parts)
[![combinations](https://img.shields.io/badge/combinations-66%20million-8E75B2.svg)](#the-parts)

[Install](#install) · [Usage](#usage) · [The parts](#the-parts) · [How it works](#how-it-works) · [Built on](#built-on) · [Design notes](docs/BEE_PORTRAIT_SYSTEM.md)

![eight generated bees](docs/examples.png)

<sub>Randomly generate 66,451,968 bee portraits</sub>

</div>

---

## introduction

I have set up a number of sprite parts, shipped with this repo, so no api key or any payments are needed. Portraits are generated in a sixth of a second, with 66 million possible combinations. The only dependency is Pillow.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/khayreali/buzz-bee-portraits/main/install.sh | sh
```

If you already have a clone, run `./install.sh` from inside it instead.

The installer copies the skill, the tools and the parts into
`~/.buzz/.agents/skills/bee-portrait/`, then links that directory into every agent
runtime set up in your nest, because each runtime only reads its own skill folder i.e. `.claude/skills`

Restart your agent and `bee-portrait` appears in its skill list. Alternatively, just refresh the page.

---

## Usage

```bash
python3 bin/make_bee.py --seed 7 --out bee.png
```

And choices are printed.

```
wrote bee.png
  antennae  elbowed--pencil-stub
  nose      pinched-top
  mouth     two-teeth
  eyes      button
  headwear  watermelon-rind
  colour    moss
  seed      7
```

Leave the seed off and you get a different bee every time. Give the same seed twice
and you get the same bee, byte for byte.

### Choosing parts yourself

Every slot has a flag. Anything you do not name is still picked at random.

```bash
python3 bin/make_bee.py --colour teal --antennae coil--ball --eyes wide-awake --out bee.png
python3 bin/make_bee.py --headwear none --out plain.png
```

| Flag | What it does |
| --- | --- |
| `--seed` | Same seed, same bee |
| `--colour` | A name from `--list colour`, or a hex value like `#D9A21B` |
| `--size` | Output size in pixels, default 384 |
| `--antennae` `--eyes` `--nose` `--mouth` `--headwear` | Pick one by name, or `none` |

List what a slot holds:

```bash
python3 bin/make_bee.py --list eyes
python3 bin/make_bee.py --list colour
```

### Putting it on an agent

```bash
buzz upload file --file bee.png
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

## The parts

| Slot | Parts | Always drawn |
| --- | --- | --- |
| `antennae` | 22 | yes |
| `eyes` | 24 | yes |
| `nose` | 23 | yes |
| `mouth` | 24 | yes |
| `headwear` | 18 | about one bee in three |

---

## How it works

The hard part of a parts library is that a clay look is mostly lighting. Cut an
antenna out of one finished portrait and paste it onto another and it is lit from
the wrong side, sits in front of the wrong shadow, and looks stuck on.

So no part was ever drawn on its own. Each one was generated onto **the same blank
grey body**, and the part is recovered by subtracting that body back out.

```
sprites/base.png            one blank body, lit from the upper left
sprites/parts/<slot>/*.png  that same body with exactly one feature added
```

Because every part was drawn onto an identical body under an identical light, they
all agree with each other. The small shadow a part casts onto the clay comes along in
the subtraction, so nothing floats.

The base is neutral grey on purpose. Grey means its brightness is pure shading, so
recolouring maps that shading onto any colour and the clay still looks like clay.
Parts that are body coloured, like antennae and noses, are recoloured with the body.
Parts with their own colours, like eyes and hats, keep them.

---

## What is in the repository

```
bin/make_bee.py       assemble a bee from the parts, offline
bin/parts.py          extraction, masking and recolouring
sprites/base.png      the blank body every part was drawn onto
sprites/parts/        the parts themselves
sprites/manifest.json which parts passed review, and which recolour
sprites/bin/          the tools that draw new parts
skills/bee-portrait/  the skill an agent loads
tests/check_repo.py   the checks continuous integration runs
docs/                 the design reasoning
```

---

## Built on

| | |
| --- | --- |
| [block/buzz](https://github.com/block/buzz) | The platform these portraits are for, and the source of the three reference bees. Apache-2.0. |
| [Gemini 3 Pro Image](https://aistudio.google.com/) | Drew every part. Only needed to add new ones, never to use them. |
| [Pillow](https://python-pillow.org/) | Does all the compositing and recolouring. |
| Python 3 | The only thing you need installed. |

---

## Licensing and attribution

This repository is licensed under Apache-2.0. See `LICENSE` and `NOTICE`.

The three reference portraits in `refs/` are derivative works. They come from
https://github.com/block/buzz, Copyright 2026 Block, Inc., also Apache-2.0, cropped to
square busts on a white background and resized. `refs/LICENSE` carries the attribution
notice and the statement of changes, and `refs/fetch.sh` re-derives the files from the
untouched originals if you want to verify that provenance.

Apache-2.0 section 6 grants no rights in trade names or trademarks, and a mascot is
exactly the sort of thing that functions as brand identity. So, plainly: this is not
Block branding, it is not endorsed by Block, and nothing here implies any relationship
with Block. Generate bees for your own roster, and do not adopt Fizz, Honey or Bumble
as your own identity. That is what the licence files say, and it is not legal advice.

---

## Further reading

[docs/BEE_PORTRAIT_SYSTEM.md](docs/BEE_PORTRAIT_SYSTEM.md) has the design reasoning:
why the parts are stored as whole bodies rather than cut out layers, why written
descriptions beat sprites for generating them, and what survives at small sizes.
