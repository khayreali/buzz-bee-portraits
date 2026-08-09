# Sprite parts

Raw generations, one image per part. Each is the blank base with exactly one
feature added, so a part is recovered by subtracting `base.png` from it. That
subtraction is what keeps the lighting and the contact shadow consistent, and
it is why the parts are stored this way rather than as cut out layers.

```
base.png            the blank body every part was drawn onto
parts/<slot>/*.png  base + one feature
bin/batch.py        generates a slot, and the quality gate
bin/assemble.py     extraction, masking and recolouring
bin/mix.py          picks parts at random and builds a whole bee
```

Do not regenerate `base.png` without regenerating every part. Every part is
tied to this exact base and a different one will not subtract cleanly.
