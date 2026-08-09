"""Stack clay parts onto the blank base and recolour the result."""
import pathlib
from PIL import Image, ImageChops, ImageFilter
from collections import deque
import colorsys

HERE = pathlib.Path(__file__).resolve().parent
SPRITES = HERE.parent
BASE = str(SPRITES / "base.png")

# Measured from the base: clay never rises above this, and the shadow it
# throws onto the paper never falls below it. So one number separates
# "clay, recolour it" from "shadow, leave it grey".
CLAY_MAX = 0.83
FLOOD = 0.86


def lum(r, g, b):
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def paper_mask(img):
    """Flood the background in from the border, so the drop shadow goes too."""
    w, h = img.size
    px = img.convert("RGB").load()
    seen = [[False] * w for _ in range(h)]
    q = deque()
    edge = [(x, y) for x in range(w) for y in (0, h - 1)]
    edge += [(x, y) for y in range(h) for x in (0, w - 1)]
    for x, y in edge:
        if not seen[y][x] and lum(*px[x, y]) > FLOOD:
            seen[y][x] = True
            q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and lum(*px[nx, ny]) > FLOOD:
                seen[ny][nx] = True
                q.append((nx, ny))
    m = Image.new("L", img.size, 0)
    mp = m.load()
    for y in range(h):
        for x in range(w):
            if not seen[y][x]:
                mp[x, y] = 255
    return m


def extract(base, path):
    img = Image.open(path).convert("RGB")
    if img.size != base.size:
        img = img.resize(base.size)
    d = ImageChops.difference(base, img).convert("L")
    mask = d.point(lambda v: 0 if v < 10 else (255 if v > 40 else int((v - 10) * 255 / 30)))
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    layer = img.convert("RGBA")
    layer.putalpha(mask)
    return layer


def tint(layer, target):
    """Recolour clay, keeping its shading. Anything lighter than clay is a
    shadow on the paper and is left alone."""
    tr, tg, tb = [c / 255.0 for c in target]
    th, ts, tv = colorsys.rgb_to_hsv(tr, tg, tb)
    src = layer.load()
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    dst = out.load()
    for y in range(layer.size[1]):
        for x in range(layer.size[0]):
            r, g, b, a = src[x, y]
            if a == 0:
                continue
            l = lum(r, g, b)
            if l > CLAY_MAX:
                dst[x, y] = (r, g, b, a)
                continue
            v = min(1.0, max(0.0, tv * (l / 0.62)))
            nr, ng, nb = colorsys.hsv_to_rgb(th, ts, v)
            dst[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return out


def build(colour, parts, base=None, clay=None):
    base = base or Image.open(BASE).convert("RGB")
    clay = clay if clay is not None else paper_mask(base)
    canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
    body = base.convert("RGBA")
    body.putalpha(clay)
    canvas.alpha_composite(tint(body, colour))
    for path, body_coloured in parts:
        layer = extract(base, path)
        canvas.alpha_composite(tint(layer, colour) if body_coloured else layer)
    return canvas.convert("RGB")


if __name__ == "__main__":
    parts = [("v_ant.png", True), ("v_eye.png", False),
             ("v_nose.png", True), ("v_mouth.png", True)]
    colours = [("amber", (217, 162, 27)), ("teal", (31, 122, 120)),
               ("pink", (191, 110, 116)), ("cobalt", (52, 86, 178))]
    base = Image.open(BASE).convert("RGB")
    clay = paper_mask(base)
    W = base.size[0]
    sheet = Image.new("RGB", (W * len(colours), W), "white")
    for i, (name, col) in enumerate(colours):
        bee = build(col, parts, base, clay)
        bee.save(f"final_{name}.png")
        sheet.paste(bee, (i * W, 0))
    sheet.save("final_sheet.png")
    print("wrote final_sheet.png")
