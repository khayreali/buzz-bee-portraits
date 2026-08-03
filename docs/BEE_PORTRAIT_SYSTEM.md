# The Bee Portrait System

This is the reasoning behind the generator in `bin/`. The README tells you how to
run the tools. This document tells you why they work the way they do, what was
measured, and what is still guesswork.

Everything here was derived by downloading the three shipped portraits, Fizz,
Honey and Bumble, and examining them at full resolution. None of it is inferred
from someone's description of what a bee looks like.

## The constants, which never vary

These are what make a new portrait read as part of the same family. Change any of
them and the set stops looking like a set.

| Element | Specification |
|---|---|
| Medium | Claymation or plasticine. Matte surface, subtle thumbprint texture, visibly handmade |
| Lighting | Soft even studio light, gentle drop shadow beneath |
| Background | Pure white, with a thin light-grey circular ring vignette |
| Format | 384 by 384 PNG, square |
| Head | Rounded cube, front-facing, centred, filling most of the frame |
| Crop | Bust. The head is cut off by the bottom edge. No body, no legs |
| Eyes | Two large rounds, off-white cream sclera, dark grey-brown pupils |
| Wings | Two, behind the head, spreading left and right in the lower half |
| Antennae | Two, rising from the top of the head |

Every one of those appears verbatim in the prompt template inside
`bin/assemble_bee.py`, which is why that template is a single fixed string with a
handful of holes in it rather than something assembled freely.

## The variables, which is where meaning lives

Four dials. Each shipped bee sets all four, and they agree with each other.

### Colour, the primary identifier

Fizz is a chartreuse or olive yellow-green. Honey is a terracotta, a warm
red-orange. Bumble is a cobalt blue. One saturated clay hue per bee, well
separated on the wheel. This is what you recognise at member-list size, so it does
the most work of anything in the system.

### Antennae, the role signature

This is the cleverest part of the shipped set and the rule most worth protecting.
The antennae encode what the agent does.

Fizz has tight coiled springs: spring-loaded, kinetic, ready to go. A maker. Honey
has smooth open curves with soft ball tips: warm, unhurried, approachable. Bumble
has straight thin stalks each topped with an extra eyeball, like periscopes. A
researcher who is looking at things, with two more eyes than anybody else.

Bumble is the proof that the idea works. You can tell that bee investigates things
before reading a single word about it.

### Face detail

Fizz has a large drooping nose and a small mouth blob. Honey has a long nose and
no visible mouth. Bumble has no nose at all and one wide flat straight mouth bar.

### Chest marking

Fizz has two horizontal stripes low on the chest. Honey has pale square blocks,
which read as honeycomb. Bumble has soft dots and dimples.

## Why written descriptions and not sprites

The obvious way to build a generator like this is a sprite library: draw fifty
antenna tips once, then composite the chosen one onto a head. That was tried and
it does not work.

Two measurements killed it. First, the light angle varies by about 40 degrees
across the three shipped portraits, so a sprite lit correctly for one head is lit
wrongly for another. Second, the contact halo where a raised feature meets the
head is host-dependent, varying by between 2.7 and 22.8 units of lightness
depending on which portrait it sits on. A sprite has to bake in one halo, and it
will be wrong almost everywhere.

So the library holds sentences instead, and the model renders the whole head at
once with the sentences filled in. The cost is that output is not deterministic.
The benefit is that the lighting and the contact shading are always internally
consistent, because they were never assembled from parts.

This is also why growing the library is cheap. A new entry is one line of English.
There is no drawing, no schema change, and no registration step.

## Why the reference portraits are sent with every request

`bin/generate_bee.py` attaches the reference portraits to the same request as
inline images, alongside the text prompt. The style constants are shown, not
described.

This is the single highest-leverage decision in the pipeline. Matte polymer clay
with thumbprint texture, a thin grey ring vignette, and that particular soft even
studio light are all things you can spend a paragraph on and still not get. Shown
three real examples, the model reproduces them without any prompt gymnastics, and
the prompt is then free to spend its words on the parts that actually vary.

It also means the system degrades gracefully. Swap the reference portraits for a
different set and the whole family changes style, while the component library
carries on working unchanged.

## References carry composition too, not only style

This was learned the expensive way, by running the clone path rather than
assuming it worked.

The portraits in `block/buzz` are full standing figures on a transparent
background. The portraits this system makes are bust crops on white. Sending the
standing figures as references produced output that was correct in medium and
wrong in framing: no bottom edge crop, a visible torso with arms, and, worse, the
headwear slid off the head and onto the chest. The prompt asked for a bust and
the references showed a full figure, and the references won.

So the portraits in `refs/` are crops, not the originals, and they are committed
so that a clone works without downloading anything. `refs/fetch.sh` re-derives
them from `block/buzz` for anyone who wants to check the provenance rather than
trust it, and continuous integration runs it on every change to prove the
committed files still match. The square is
anchored on the head with deliberate headroom above the antennae. That headroom
is not cosmetic. Without it the model has nowhere to put a hat and puts it on the
chest instead.

Two smaller findings from the same work:

The ring vignette should not be drawn into the reference. Baking a grey circle
into the reference image made the model read it as a physical object and sculpt a
rope of clay around the bee. The prompt asks for the vignette and the model draws
it correctly on its own. Some things are better described than shown, and the
dividing line is whether the thing is part of the subject or part of the frame.

Reference resolution sets a ceiling on style fidelity. The originals are 160
pixels wide and get upscaled to 384, which is soft. Softer references give the
model less to copy, so it fills the gap with its own defaults, which run more
detailed and more sculptural than the flat clay look. Output from a fresh clone
is on model but slightly richer than portraits made from sharper references. If
you already have crisp bust portraits, point `BEE_REFS` at them.

## Headwear needs an anchor, chest does not

The chest line reads "Across the lower chest, ...". The headwear line used to
read "It is wearing ...", with no anchor at all.

For an actual hat that is harmless, because a hat implies a head. For the rest of
the vocabulary it is not. A pea pod, a cheese wedge, a paper boat and a thread
spool are all objects first and headwear second, and with nothing anchoring them
the model placed them wherever the composition had room, which was usually the
chest.

The template now renders "On top of its head it is wearing ...". One clause, and
it fixed the whole class at once. The general lesson is that every slot in a
generated prompt needs to say where it goes, and the slots you never had trouble
with are the ones whose names already carry the location.

## The antennae grammar

An antenna has two halves and they mean different things.

| Part | Encodes | Grammatical role |
|---|---|---|
| Tip | What the agent operates with, its instrument | noun |
| Stalk | How it works, its posture | adverb |

Read back against the shipped set, they agree:

| Bee | Stalk, the posture | Tip, the instrument | Reads as |
|---|---|---|---|
| Fizz | tight coil, stored energy | plain small ball, no special organ | a generalist, spring-loaded |
| Bumble | straight, upright, alert | eyeball, an added sense organ | perceives, goes looking |
| Honey | open curve, unhurried | soft large ball, presence with no tool | receives, approachable |

Three rules keep this working.

Describe the job as a verb, not a title. The antenna encodes "leaves a mark", not
"writer". Titles break the moment one agent does two jobs. Verbs do not.

One tip instrument per bee, and first claim owns it. A second bee with eyes on
stalks does not read as also observant, it reads as a copy. If a new role's
obvious instrument is taken, find the verb that distinguishes it and draw that
instead. This is what the `taken_by` field and the `--respect-taken` flag exist
for, though the shipped values name somebody else's roster and you will want to
replace them with your own.

The stalk must read at 24 pixels, and the tip only needs to read at 48. The two
halves have different legibility thresholds and they line up with the noun and
adverb split: the adverb reads at a distance, the noun reads on approach. The next
section has the measurement behind this.

Some vocabulary for roles that tend to come up:

| Role | Verb | Stalk | Tip | Why not the obvious thing |
|---|---|---|---|---|
| Writer | leaves a mark | one straight, one mid-bend, a thought in progress | a teardrop of ink about to fall | a nib is the obvious choice and it dies at 24 pixels |
| Reviewer | weighs | matched, level, perfectly symmetrical | a small flat pan on each, so the two antennae are the scale | not a magnifier, because that is looking, and looking is already taken |
| Scheduler | announces the hour | asymmetric, one raised and one low, like hands at ten past ten | a small bell | not a clock face, because that is an icon rather than an instrument, and a face will not read small |
| Watcher | keeps a light on | wide-splayed, angled outward for coverage | a lit lamp or beacon | emphatically not eyes, because a watcher makes things visible rather than going to look |

The reviewer is the strongest of these. Two antennae naturally form a balance
scale, so the pose does all the work with no added detail.

## What actually reads at small sizes

The three shipped portraits were downsampled with Lanczos to 24, 32 and 48 pixels
and inspected, first as alpha-thresholded silhouettes and then again in colour.
Both runs agreed on the headline result and disagreed usefully on the method.

At 24 pixels in silhouette, all three collapse to near-identical dark masses with
similar notches. Antenna shape is not recoverable at all. The eyeball, the coil
and the ball are indistinguishable from one another.

At 24 pixels in colour, the three are instantly separable, and separable almost
entirely by hue. The antennae are still told apart, but as wiggly, smooth-curved
and straight-with-beads. That is the stalk, not the tip. No tip instrument is
identifiable, including the two that ship.

At 48 pixels the tips appear. Ball, eyeball, hexagon, pan, bell, lamp and teardrop
all work here. Pen nibs, clock faces, gear teeth and anything lettered still fail.

Two conclusions follow, and one correction.

The conclusion is the split threshold in the third rule above. The stalk is a
24-pixel feature and the tip is a 48-pixel feature. The practical consequence is
that stalk posture is scarcer than tip instrument. There are perhaps five or six
distinguishable postures, so spend them as carefully as you spend colours. Tip
vocabulary is effectively unlimited.

The correction is that the silhouette was the wrong instrument, not merely the
wrong size. Alpha-thresholding destroys internal contrast, and internal contrast
is exactly how a tip reads. Bumble's eyeballs are cream and charcoal beads against
white, and in silhouette they become a featureless blob, which understates what
survives. Any future legibility test should be run in colour.

An earlier version of this guidance said the tip must survive the 24-pixel
silhouette test. That was wrong twice over, and it would have rejected tips that
two shipped bees already use successfully.

## Colour is the scarce axis, and it is measurable

`bin/clay_colours.py` exists because colour separation is the binding constraint
on how many bees a roster can hold, and because eyeballing a swatch is not a
reliable way to judge it.

The tool measures the saturated pixels of a portrait and averages them in CIELAB.
Run against the three shipped references, `python3 bin/clay_colours.py measure
refs` gives:

```
bumble    #4773A3   lightness  47.2  muted steel blue
fizz      #A79F2F   lightness  64.3  pale vivid chartreuse
honey     #A34534   lightness  41.8  deep brick red
```

Pairwise colour distances, Euclidean in CIELAB, are 89.0 between Bumble and Fizz,
71.3 between Bumble and Honey, and 59.2 between Fizz and Honey. So the three
shipped portraits sit at a floor of 59.2, and that number is the calibration for
everything else here. It is a spacing that demonstrably works.

Be clear about what that floor is measured over. It is the three portraits in
`refs/`, and nothing else. `measure refs --write` builds `roster.json` from those
three files alone, so when the tool prints "existing roster floor" it is
reporting the spacing of the shipped set, not the spacing of your agents. Every
number in this section is reproducible from a fresh clone precisely because the
population is that small and that fixed. Point the tool at your own portraits and
you will get different numbers, which is the point of it being a tool rather than
a table.

Note that lightness is doing real work here, spanning 42 to 64. An earlier
analysis claimed lightness was flat across the three and concluded that hue was
carrying identification unaided. That was measured with the lightness component of
HLS, which is simply the midpoint of the largest and smallest channel and carries
no perceptual weighting. Re-measured properly in CIELAB the spread is 22.5
points. Lightness is a working second axis, which is why the tool packs in three
dimensions rather than sorting by hue.

### The packing cliff

Farthest-point packing inside a gamut restricted to clay-plausible colours,
lightness 35 to 70 and chroma 25 to 62, with the shipped three pinned, gives this:

| Total colours | Floor |
|---|---|
| 4 | 59.2 |
| 5 | 58.5 |
| 6 | 45.4 |
| 8 | 37.9 |
| 10 | 36.3 |
| 14 | 33.5 |

Reproduce any row by running `python3 bin/clay_colours.py measure refs --write`
once and then `python3 bin/clay_colours.py sample --count N`. Watch the
arithmetic: `--count` is the number of new colours, and the three shipped ones are
already pinned, so a total of 6 means `--count 3`. The floor is the last figure
the tool prints, and it names the total alongside it.

The fourth colour is free. It lands at 59.2, which is exactly the spacing the
shipped three already have, so it costs nothing at all. The fifth is very nearly
free, giving up 0.7 of a point to 58.5. Six is where it breaks. The floor drops
13 points in a single step to 45.4, and from there it grinds slowly downward. The
gamut restriction matters, because an unconstrained solver returns neon colours
that pack beautifully and do not look like clay.

The threshold `clay_colours.py` warns at is 47, which sits between the comfortable
five-colour floor of 58.5 and the six-colour one of 45.4.

### A worked example, and why the tool is worth running

Amber gold is the most obviously bee-appropriate colour there is, and it is one of
the worst available slots on the wheel. Running

```
python3 bin/clay_colours.py check '#D9A21B'
```

reports a distance of 24.3 to Fizz, well under the threshold of 47, so the two
would be hard to tell apart at member-list size. The same line of output shows
lightness 69.9 and chroma 69.9. Only one of those is a problem. The lightness
scrapes inside the 35 to 70 band with a tenth of a point to spare, while the
chroma is 7.9 over the ceiling of 62, so the colour falls outside the clay gamut
on chroma alone. It is too saturated to read as plasticine, not too bright.

Pushing it darker toward bronze does not rescue it, because darkening moves along
the same hue rather than away from it. A bronze such as `#B8860B` comes out at
21.6 from Fizz, which is closer than the gold was.

Both of those distance figures assume `roster.json` exists. Run `measure refs
--write` first, or `check` has nothing to compare against and says so.

The general lesson is not about any particular bee. It is that a colour which
looks clearly different on a swatch, viewed large and next to nothing, can still
be the wrong choice at the size a member list renders. Run the check before
committing.

### Buying fewer colours and reusing them

Since posture also reads at 24 pixels, colour and posture can be used together
rather than colour alone. Partition the roster into posture classes and let colour
identify the individual within a class:

| Class | Posture | Domain | Confirmed at 24 pixels |
|---|---|---|---|
| Makers | coiled | build, generate, ship | yes, Fizz |
| Talkers | open curve | write, explain, converse | yes, Honey |
| Analysts | straight upright | research, review, watch | yes, Bumble |
| Stewards | symmetrical arc | orchestrate, schedule, hold state | untested, no bee wears it |

Three classes of five is fifteen bees drawing on only five colours, and five
colours pack to a floor of 58.5, within a point of the 59.2 the shipped three
enjoy. So every comparison a viewer actually makes stays at close to the spacing
that is known to work. The fourth class is a reasonable extrapolation and has
never been tested against the other three. Test it before committing to it.

There is one place colour reuse breaks. Two bees sharing a colour collide anywhere
the posture is not visible: a 16-pixel favicon, a colour-only status dot, a chart
legend keyed to agent colour. Reuse is safe wherever the actual portrait renders.
If a surface shows colour without the portrait, that surface needs fully separated
colours instead.

### A note on colour naming

CIELAB hue is not HSL hue. In CIELAB, sRGB red sits near 40 degrees and blue near
306, so hand-set hue bounds copied from a colour wheel put Bumble's cobalt in the
indigo bucket. Bumble measures at a CIELAB hue of 269.3, which a wheel would call
indigo and which the tool correctly calls steel blue. The `HUE_ANCHORS` list in
`clay_colours.py` is therefore a list of angles computed from real hex colours
rather than bounds read off a wheel, and naming is by nearest anchor.

## The nine slots and what each is for

| Slot | Entries | Role |
|---|---|---|
| `base_colour` | 40 | The primary identifier. Ten hand-picked, thirty procedurally packed |
| `antennae` | 100 | The stalk. Posture, meaning how the agent works |
| `antenna_tip` | 100 | The instrument. What the agent operates with |
| `eyes` | 100 | Expression |
| `nose` | 100 | Expression |
| `mouth` | 100 | Expression |
| `chest` | 100 | Marking |
| `headwear` | 100 | Decoration only, and rare |
| `glasses` | 100 | Filled but switched off by default |

That is about 4 quadrillion combinations across the live slots, which is a
meaningless number by itself. The number that matters is that the antennae slot
has 100 distinct three-word openings across its 100 entries, so nothing reads as a
filled-in template when it lands in the prompt.

Two rules are worth stating explicitly, because they are easy to break while
extending the library.

Headwear is decorative and never encodes role. A bee in a cowboy hat is not a
cowboy, it is a bee wearing a cowboy hat. Role lives in the antenna tip. Keeping
these separate is what lets the hat vocabulary stay wide open without competing
with the part that carries meaning.

Accessories are rare on purpose, roughly one bee in six. If every bee has a hat,
the hat identifies nobody. This is enforced in the assembler rather than in the
library, so it applies automatically to any hat you add.

The glasses slot is complete and disabled, by the original author's decision for
their own roster. The entries are kept rather than deleted, so turning the slot on
is a one-line edit to `_disabled_slots` in `components.json`. When glasses are
drawn, the assembler stops describing the eyes, because describing both makes the
model draw both.

## The generation pipeline

The model is Gemini 3 Pro Image, called directly at
`generativelanguage.googleapis.com`. Nano Banana Pro is the same model under a
different name, so there is no reason to go through a reseller or a subscription.

The request asks for image output only, a 1:1 aspect ratio, and an image size of
1K, 2K or 4K. The reference portraits go into the same request as inline PNG
parts, ahead of the text. If a seed is supplied it is passed to the model as well
as used for slot selection, so a seed reproduces the choices and, as far as the
model allows, the image.

Output arrives at the requested size and is downsampled to 384 pixels square to
match the shipped set, unless `--keep-full` is passed. The downsample step also
rewrites the pixel data into a fresh image, which drops the generator's provenance
metadata, because some relays reject uploads that carry it.

Cost is roughly 13 to 14 cents per image at 1K and roughly 24 cents at 4K.

## Adding a new bee

1. Pick a colour no existing bee owns, and verify it with
   `clay_colours.py check` rather than by eye.
2. Design the antennae around the job. Ask what the agent is physically doing,
   then build that into the stalk and the tip. This is the step people skip, and
   it is the one that makes a set feel designed rather than recoloured.
3. Pick one face quirk and one chest marking. Keep both simple.
4. Change nothing else. Every constant in the first table stays fixed.

## The blank base model, and a finding about wings

There is a companion prompt that renders a featureless grey maquette: uniform
neutral clay, no eyes, no nose, no mouth, no antennae, no markings, no colour. It
is the unpainted model the slots get added to, and it is useful as a design
reference. No agent ever wears it.

It had one persistent defect worth recording, because the fix generalises.

The blank consistently rendered four wings rather than two, a broad upper wing
plus a smaller lobe below it on each side, which is a real insect's forewing and
hindwing pair. Coloured bees never do this. Only the blank does, because with no
face to anchor the stylisation the model falls back to actual insect anatomy.

Three rounds of escalating the count failed. "Exactly two wings", "two wings only,
not four", "one on the left, one on the right", none of it worked. Stating the
count first, in a paragraph labelled as the most important thing in the picture,
also failed. Removing every negation from the prompt failed. Dropping the word
"bee" failed, which makes sense once you notice that three reference bee portraits
are attached to every request regardless.

What fixed it was changing the shape word. Every organic wing noun, petal, leaf,
paddle, describes an outline that can legitimately have lobes, and the model
resolved that ambiguity toward real anatomy. Describing each wing as "a plain
half-disc of clay, like a semicircle" gives a rigid geometric primitive with
nowhere to put a second lobe. Adding an explicit part count as a positive fact,
"it is made from three pieces of clay and three only", listing the head and the
two wings, reinforced it.

Across 28 test images, the winning variant went from zero out of three on the old
wording to eight out of nine on the new one. The general lesson is that this model
obeys shape primitives far more reliably than it obeys counts. When a count is
being ignored, rename the thing being counted into a shape that cannot be
subdivided, rather than shouting the number louder.

Two honest caveats. First, the fix introduced a separate problem. The part-count
enumeration invites a whole-object product shot, and the bottom crop, where the
head is cut off by the frame edge, landed on only four of those nine runs. The
failing runs all reintroduce a drop shadow under a floating head. Wings and crop
landing together is closer to a coin flip than to solved, and anyone picking this
up again should attack the shadow rather than the wings. Second, an initial three
out of three result was reported as shipping quality and a nine-sample replication
corrected it. Treat every rate here as indicative rather than measured, and
generate two or three if you ever rebuild the blank.

## Scope and open questions

The analysis covers Fizz, Honey and Bumble at full resolution. Those are the three
portraits distributed with Buzz and the three the fetch script downloads.

The steward posture, a symmetrical arc, has not been tested at small sizes against
the other three. It is an extrapolation.

The 47-point collision threshold is calibrated against a three-bee sample. It sits
between the measured five-colour and six-colour floors, which is a defensible
place to put it, but it has not been validated against anybody actually failing to
tell two bees apart.

The legibility findings come from downsampling three images and looking at them.
They are consistent, and they match what the packing numbers predict, but they are
not a user study.
