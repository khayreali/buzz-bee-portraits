# Contributing

The most useful contribution is almost always a component library entry. That is
what makes the bees varied, and it needs no Python at all.

## Adding components

Open `bin/components.json`, find the slot you want, and add an entry:

```
{"id": "coil", "phrase": "two tightly coiled spring antennae"}
```

Two rules that matter more than they look:

The phrase is pasted into the prompt word for word. Write it the way you would
describe the shape to somebody sculpting it, not the way you would tag it in a
database. "a soft bucket hat with a droopy brim" works. "bucket_hat" does not.

The entry has to survive being small. Agent portraits are looked at in a member
list at around 24 to 48 pixels. If your idea collapses into something the library
already has at that size, it adds nothing. A snowball, a pebble, a marble and an
egg are all the same circle once they are that small.

Read the `_hard_rules` key in the same file before you write for `headwear` or
`antenna_tip`. Headwear is decorative and never encodes what an agent does. The
antenna tip is the slot that carries meaning.

Do not add a `taken_by` field. Those exist so a specific roster keeps its own
components, and they are wrong for everybody else already.

## Running the checks

```
python3 tests/check_repo.py
```

That validates the library, the pack layout and the skill frontmatter, and it
assembles fifty prompts to make sure nothing broke. It catches duplicate
identifiers and, more usefully, two entries whose descriptions are the same
sentence, which the image model cannot tell apart.

Continuous integration runs the same checks on Python 3.9, 3.12 and 3.13,
installs the skill into a temporary directory, and re-derives the reference
portraits from block/buzz to confirm the committed copies still match.

## Changing the prompt template

Be careful here, and test with real images rather than reasoning about it.
`bin/assemble_bee.py` holds the template. Every slot needs to say where it goes
on the bee. The headwear line once said only "It is wearing", with no anchor, and
the model put pea pods and cheese wedges on the chest until it was changed to "On
top of its head it is wearing".

`--dry-run` is free and shows the assembled prompt without calling the model, so
use it for anything you can check by reading.

## Style

No em dashes, use commas. No abbreviations. Minimal comments in code, and only
where the reason is not obvious from reading. Plain mechanisms, ordinary loops
over clever one liners. Limited markdown in documentation.

## Licensing

Contributions are made under Apache-2.0, the same licence as the repository.
Do not add images you do not have the right to redistribute. The reference
portraits in `refs/` are derivative works of Apache-2.0 material from block/buzz
and are documented in `refs/LICENSE`, so anything new in that directory needs the
same treatment.
