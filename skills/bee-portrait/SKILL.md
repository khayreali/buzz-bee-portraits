---
name: bee-portrait
description: >
  Make a clay bee portrait for a Buzz agent profile picture from a library of
  shipped parts, then upload it and apply it. Needs no API key and costs
  nothing. Use when a new agent needs an avatar, when an agent is still wearing
  a placeholder icon, or when asked for a bee that does not look like the ones
  already on the roster.
version: 2
---

# Bee portrait

Assemble a claymation bee from parts that ship with this skill. No network call,
no API key, no cost. One command.

## Make one

```bash
python3 <skill>/bin/make_bee.py --seed 7 --out bee.png
```

`<skill>` is the directory this file sits in. The scripts and the parts are
inside it, so there is never a separate checkout to find.

It prints what it chose and writes a JSON file beside the image recording the
same thing, which is enough to rebuild that exact bee later:

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

Leave `--seed` off for a different bee every time. The same seed always gives
the same bee, byte for byte.

## Choose parts deliberately

Anything you do not name is still picked at random, so you can fix one thing and
let the rest fall out.

```bash
python3 <skill>/bin/make_bee.py --colour teal --eyes wide-awake --out bee.png
python3 <skill>/bin/make_bee.py --headwear none --out plain.png
```

| Flag | What it does |
| --- | --- |
| `--seed` | Same seed, same bee |
| `--colour` | A name from `--list colour`, or a hex value like `#D9A21B` |
| `--size` | Output size in pixels, default 384 |
| `--antennae` `--eyes` `--nose` `--mouth` `--headwear` | Pick one by name, or `none` |

See what a slot holds before choosing:

```bash
python3 <skill>/bin/make_bee.py --list eyes
python3 <skill>/bin/make_bee.py --list colour
```

Headwear is drawn on roughly one bee in three. That is deliberate. A hat on
every bee reads as clutter rather than as character.

There is no eyewear slot. Glasses were built and dropped, because the lenses came
out opaque and covered the eyes.

## Choosing a colour that does not collide

If the agent joins a roster that already has bees, look at what is taken before
picking. Two agents in the same colour are harder to tell apart in a member list
than any other kind of similarity, because at small sizes colour does most of
the work.

```bash
python3 <skill>/bin/make_bee.py --list colour
```

Pick one nobody is using, or pass a hex value of your own.

## Look at it before you keep it

Open the file. The things worth rejecting a bee over:

- The face is crowded. A hat over heavy eyes can turn into soup at small sizes.
  Drop it with `--headwear none`.
- The colour is close to another agent on the same roster.
- The mouth disappears against the body. Some quiet mouths vanish on dark clay.

Generating another costs nothing, so regenerate freely rather than settling.

## Applying it

Two steps, and both matter.

```bash
buzz upload file --file bee.png
buzz users set-profile --avatar <url>
```

`buzz users set-profile` updates the current identity only. It signs a profile
event with the key of whoever runs it, and there is no flag naming a different
agent. So you can make a portrait for another agent, but you cannot apply it for
them. Hand over the uploaded address and ask that agent to run `set-profile`
itself. Running it yourself will quietly put the picture on your own face.

The address is not public. The relay requires a signed read and current relay
membership on every media request, so fetching one without authenticating
returns 401. The picture loads for relay members inside Buzz, and a client that
reads the profile without authenticating will not be able to show it.

**In Buzz Desktop the avatar may not stick.** Desktop stores an avatar on the
agent record and re-publishes that record whenever an agent starts and the relay
disagrees with it. A picture applied with `set-profile` alone changes the relay
but not the record, so it can be replaced on the next start. To make it durable,
set it on the agent in Desktop as well.

## Drawing new parts

Only needed to extend the library, and this is the one thing that costs money
and needs `GEMINI_API_KEY`. Making bees never touches the network.

```bash
python3 <skill>/sprites/bin/batch.py mouth 24
```

Each part is about 13 cents and 13 seconds. Google limits spending to 10 dollars
per rolling ten minutes and 250 images per day on tier 1, so one generation at a
time is the safe pace and 250 parts is a day of work.

Do not regenerate `sprites/base.png`. Every part was drawn onto that exact base
and is recovered by subtracting it back out, so a new base breaks all 111.

## When something fails

- `no manifest at ...`. The parts did not install. Run `install.sh --check`.
- `no eyes called X`. Run `--list eyes` to see the real names.
- `ModuleNotFoundError: PIL`. Install Pillow, `pip install Pillow`.
- The skill does not appear to the agent at all. The install has to be linked
  into the runtime's own skill directory. `install.sh --check` reports which
  runtimes are linked, and reinstalling creates the links.
