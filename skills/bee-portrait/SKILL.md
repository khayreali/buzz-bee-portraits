---
name: bee-portrait
description: >
  Generate a clay bee portrait for a Buzz agent profile picture, then upload it
  to the relay and apply it. Use when a new agent needs an avatar, when an agent
  is still wearing a placeholder icon, or when asked to pick a bee colour that
  does not clash with the agents you already have.
version: 1
---

# Bee portrait

This skill makes one square clay bee portrait and puts it on an agent profile.

The portrait is assembled from a component library rather than written by hand.
`bin/components.json` holds nine slots of written descriptions. A script picks
one entry per slot, joins them into an English prompt, and sends that prompt to
an image model with existing bee portraits attached. The attached portraits are
what hold the style steady, not the words.

Use it when you have just been created and have no picture, when someone asks
for a bee for a new agent, or when you need a colour that stays distinct from
the agents already on the roster. Do not use it to redesign the look. The style
constants are already in the prompt template and in the reference portraits.

## Where the files are

The skill is self contained. `bin/` and `refs/` are siblings of this file, in
the directory you loaded it from. There is nothing to clone and nothing to
download.

```
bee-portrait/
  SKILL.md
  bin/assemble_bee.py, generate_bee.py, clay_colours.py, components.json
  refs/fizz.png, honey.png, bumble.png
```

Every command below is written relative to that directory. The scripts find
`components.json` and `refs/` next to themselves, so a full path works from
anywhere and the directory you are standing in does not matter.

The usual location is `~/.buzz/.agents/skills/bee-portrait/`, but `BUZZ_NEST`
can move the whole nest, so prefer the directory this file came from.

## What you need before you start

Check these in order. The first two are enough to preview a prompt for free.

1. Python 3. Run `python3 --version`. The prompt assembler uses only the
   standard library.
2. The library and the references, `ls bin/components.json refs/*.png`. Three
   portraits ship with the skill, so this should already pass. To use different
   ones, set `BEE_REFS` to a directory of square png files, or pass paths with
   `--refs`. Without at least one reference the generator stops and says so.
3. A Gemini key, needed only for real generation. Check with
   `printenv GEMINI_API_KEY` and never print the value. In Buzz Desktop it goes
   under Settings, Agents, Agent defaults, Advanced, Environment variables. In a
   plain shell, `export GEMINI_API_KEY=your-key-here`. Keys come from
   https://aistudio.google.com/apikey

Pillow is optional. Without it, `generate_bee.py` keeps whatever resolution the
model returned instead of downsampling to 384 pixels, and prints a line saying
so. That image still works as an avatar. Pillow is only really needed for the
`measure` subcommand and the `--swatch` option of the colour tool. Install it
with `pip install Pillow` if you need those.

`refs/fetch.sh` is in the source repository, not in the installed skill. It
re-derives the shipped portraits for provenance checking. It is not a setup step.

## Preview a prompt without spending anything

```bash
python3 bin/assemble_bee.py --seed 7
```

That prints the chosen slots on the first line, then the prompt. The same seed
always gives the same bee. Try a few seeds until one reads well, then note the
number.

To see the full request path without calling the model, which is free and makes
no network call:

```bash
python3 bin/generate_bee.py --seed 7 --dry-run --out /dev/null
```

## The nine slots

`base_colour`, `antennae`, `antenna_tip`, `eyes`, `nose`, `mouth`, `chest`,
`headwear`, `glasses`. Most hold 100 written descriptions. `base_colour` holds
40, and it is the slot the colour tool extends.

Two behaviours worth knowing:

- `glasses` is switched off. It is listed under the `_disabled_slots` key in
  `components.json`, so the assembler skips it even though the entries are
  filled in. They stay in the file as dead stock.
- `headwear` appears about one time in six. Accessories are rare on purpose. If
  every bee has a hat, the hat identifies nobody. When a hat is picked it is
  rendered as "On top of its head it is wearing ...", which keeps the model from
  putting it on the chest.

## Deliberate choice versus a random seed

List the options in any slot:

```bash
python3 bin/assemble_bee.py --list antenna_tip
```

Every slot also has a matching flag on both scripts, spelled with hyphens:
`--base-colour`, `--antenna-tip`, `--headwear`, and so on. A flag takes an entry
identifier, the short name in the left column of `--list`.

```bash
python3 bin/assemble_bee.py --base-colour cobalt --antennae coil --antenna-tip lamp
python3 bin/assemble_bee.py --seed 42 --base-colour teal
```

Mix the two freely, as the second line does. Anything you name is fixed,
anything you leave out is drawn from the seeded generator.

Naming a slot explicitly also overrides the disabled list, so
`--glasses oval-wire` will put glasses on the bee. That is the only way they
come back, and the owner decision is that they stay off.

A good default is to fix the two things that carry meaning, the base colour and
the antenna tip, and let the seed handle the decorative slots. Faces and chest
markings do not need to mean anything. The tip already answers what the agent
does, and a second answer to the same question just muddles it.

## About the taken_by fields

`components.json` ships `taken_by` fields naming the original author's roster.
Seven base colours and six antenna tips are marked that way.

So `--respect-taken` will be wrong for any other roster. It will skip components
that are free for you, and it knows nothing about the components your own agents
already wear. Either edit the `taken_by` fields to match your roster before you
rely on the flag, or leave the flag off and track claims yourself.

Whichever you do, keep one antenna tip per agent. A second agent with the same
tip reads as a copy rather than as a relative.

## Picking a colour that does not collide

Colour does most of the work of telling two agents apart at small sizes, so it
is the part worth being careful about. `bin/clay_colours.py` has three
subcommands.

First, measure the agents you already have. Point it at a directory of portrait
files and write the result:

```bash
python3 bin/clay_colours.py measure refs --write
```

The directory is optional and defaults to `refs/`, so point it at your own
portraits if you have them. It reads the saturated pixels out of each file,
averages them in CIELAB, and saves `bin/roster.json`. It needs Pillow.

Run this first. Nothing else works properly until `roster.json` exists. Without
it, `check` says plainly that there is nothing to compare against, and `sample`
packs colours away from nothing, so it just returns the corners of the gamut.

Then test a colour you have in mind:

```bash
python3 bin/clay_colours.py check "#D9A21B"
```

It reports lightness, chroma and hue, says whether the colour sits inside the
clay gamut, which is lightness 35 to 70 and chroma 25 to 62, and lists the
distance to every agent on the roster. Anything under 47 is marked as colliding,
which is where two agents start to look alike at small sizes. Saturated neon
sits outside the gamut and breaks the clay look.

Or let the tool propose colours, packed as far as possible from the ones you
already use:

```bash
python3 bin/clay_colours.py sample --count 12
```

The table shows an identifier, a hex value, the distance to the nearest existing
agent, and which agent that is. Underneath it prints the separation floor for
your current roster and the floor once the new colours are added, so you can see
what each addition costs. `--step` controls the search grid and defaults to 4.0.
Lower it for a finer search and a slower run.

Two extras:

- `--json` prints entries in the exact shape `base_colour` expects, ready to
  paste into `components.json`.
- `--swatch colours.png` writes a labelled grid so you can look at them. This
  one needs Pillow.

Once a colour is in `components.json` you can name it like any other entry.

## Generating the portrait

```bash
python3 bin/generate_bee.py --seed 7 --out bee.png
```

This costs roughly 13 to 14 cents per image at the default size, so settle the
prompt with `--dry-run` first.

The flags are:

- `-o` or `--out`, required, where to write the portrait.
- `--seed`, the same seed the assembler takes. It is also passed to the model.
- `--size`, one of `1K`, `2K` or `4K`. Defaults to `1K`.
- `--refs`, one or more reference files to send instead of the default set.
- `--dry-run`, print the prompt and stop.
- `--keep-full`, skip the downsample and keep whatever the model returned.
- `--prompt-file`, use a prompt from a file instead of building one.
- `--respect-taken`, described above.
- the nine slot flags.

Three environment variables affect it. `GEMINI_API_KEY` is required. `BEE_REFS`
overrides the reference directory. `BEE_MODEL` overrides the model, which
defaults to `gemini-3-pro-image`.

After the image is written, it is downsampled to 384 pixels square and rewritten
without the generator metadata, because some relays reject uploads that carry
it. Pass `--keep-full` to skip that. If Pillow is missing the step is skipped
anyway and a line says so.

A sidecar file is written next to the portrait, `bee.json` beside `bee.png`,
recording the seed, the model, the size, the identifier chosen in every slot and
the full prompt. Keep it. It is the only way to regenerate the same bee later,
and where you look when you want a sibling with a family resemblance. There is
no sidecar with `--prompt-file`, because there are no slot choices to record.

## Look at it before you keep it

View the result at 24 and 48 pixels, not just full size. Colour does nearly all
of the identifying at 24 pixels. The antenna tip only becomes readable around
48. Squint at the outline rather than the shading, because at small sizes almost
every pixel of an antenna is edge against white.

If the tip is the same tone and the same width as the stalk, it is just more
antenna. Regenerate with a different tip rather than accepting it.

## Applying it

Two steps, and both matter.

Upload the file to the relay:

```bash
buzz upload file --file bee.png
```

That prints a descriptor including a `url`. The portrait has to be uploaded for
this to work. A profile picture is an address that clients fetch rather than a
file, so there is no local path that will do instead and no offline option.

That address is not public. The relay requires a signed read and current relay
membership on every media request, so fetching one without authenticating
returns 401. The picture loads for relay members inside Buzz, and a client that
reads the profile without authenticating will not be able to show it.

Then set it on the profile:

```bash
buzz users set-profile --avatar <url>
```

Here is the part that is easy to get wrong. `buzz users set-profile` updates the
current identity only. It signs a profile event with the key of whoever runs it.
There is no flag naming a different agent, and the agent draft commands have no
avatar field at all.

So you can generate a portrait for another agent, but you cannot apply it for
them. Hand over the uploaded address and ask that agent to run `set-profile`
itself, or ask a person to set it in Buzz Desktop. Doing anything else, such as
running the command and hoping it lands on the right profile, will quietly put
the picture on your own face.

## When something fails

- `can't open file .../bin/assemble_bee.py`. The path is wrong. The scripts sit
  next to this file, under `bin/`. Use the full path to the skill directory.
- `no such file or directory: components.json` or missing reference portraits.
  The install is incomplete. Reinstalling repairs it and keeps a copy of the
  old install beside the new one:
  `curl -fsSL https://raw.githubusercontent.com/khayreali/buzz-bee-portraits/main/install.sh | sh`
  Add `-s -- --check` to the end of that command to report the state without
  writing anything.
- `no 'x' in slot. options: ...`. You passed an identifier that does not exist.
  The message lists every valid one.
- `GEMINI_API_KEY is not set`. See the prerequisites above.
- `no reference portraits found in ...`. Either `BEE_REFS` points somewhere
  empty, or the install is missing `refs/`. Check with `ls refs/*.png`.
- `reference portrait missing: ...`. A path you passed to `--refs` does not
  exist.
- `no image returned, finishReason=...`. The model refused or stopped early.
  Change a slot and try again rather than repeating the same request.
- `no roster.json found, so there is nothing to compare against`. Run
  `clay_colours.py measure` with `--write` first.
- `ModuleNotFoundError` mentioning PIL. Run `pip install Pillow`. Only the
  `measure` subcommand and `--swatch` need it.
