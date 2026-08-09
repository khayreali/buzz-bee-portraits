"""Turn the shipped part images into a finished bee.

Every part was generated onto one blank grey base, so a part is recovered by
subtracting that base back out. The leftover difference carries the part and
the small shadow it casts onto the clay, which is why nothing looks stuck on.
"""
from collections import deque
import colorsys

from PIL import Image, ImageChops, ImageFilter

# Measured from the base. Clay never rises above this and the paper never
# falls below it, so one number separates what gets recoloured from what
# stays grey.
CLAY_MAX = 0.83
FLOOD = 0.86


def luminance(r, g, b):
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def clay_mask(image):
    """The clay body. Flooding in from the border leaves the paper behind."""
    width, height = image.size
    pixels = image.convert("RGB").load()
    seen = [[False] * width for _ in range(height)]
    queue = deque()

    edge = []
    for x in range(width):
        edge.append((x, 0))
        edge.append((x, height - 1))
    for y in range(height):
        edge.append((0, y))
        edge.append((width - 1, y))

    for x, y in edge:
        if not seen[y][x] and luminance(*pixels[x, y]) > FLOOD:
            seen[y][x] = True
            queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if not seen[ny][nx] and luminance(*pixels[nx, ny]) > FLOOD:
                    seen[ny][nx] = True
                    queue.append((nx, ny))

    mask = Image.new("L", image.size, 0)
    out = mask.load()
    for y in range(height):
        for x in range(width):
            if not seen[y][x]:
                out[x, y] = 255
    return mask


def extract(base, part_path):
    """Whatever the part added, as a layer with soft edges."""
    image = Image.open(part_path).convert("RGB")
    if image.size != base.size:
        image = image.resize(base.size)
    difference = ImageChops.difference(base, image).convert("L")
    mask = difference.point(
        lambda v: 0 if v < 10 else (255 if v > 40 else int((v - 10) * 255 / 30))
    )
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    layer = image.convert("RGBA")
    layer.putalpha(mask)
    return layer


def tint(layer, colour):
    """Recolour clay while keeping its shading.

    The base is flat grey, so its brightness is pure shading. Mapping that
    brightness onto a colour keeps every highlight and crease. Anything
    lighter than clay is a shadow on the paper and is left alone.
    """
    red, green, blue = [c / 255.0 for c in colour]
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)
    source = layer.load()
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    target = out.load()
    for y in range(layer.size[1]):
        for x in range(layer.size[0]):
            r, g, b, a = source[x, y]
            if a == 0:
                continue
            light = luminance(r, g, b)
            if light > CLAY_MAX:
                target[x, y] = (r, g, b, a)
                continue
            v = min(1.0, max(0.0, value * (light / 0.62)))
            nr, ng, nb = colorsys.hsv_to_rgb(hue, saturation, v)
            target[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return out


def build(base, mask, colour, chosen, slots):
    """Stack the chosen parts onto a recoloured body."""
    canvas = Image.new("RGBA", base.size, (255, 255, 255, 255))
    body = base.convert("RGBA")
    body.putalpha(mask)
    canvas.alpha_composite(tint(body, colour))
    for slot in slots:
        path = chosen.get(slot)
        if path is None:
            continue
        layer = extract(base, path)
        if slots[slot]:
            layer = tint(layer, colour)
        canvas.alpha_composite(layer)
    return canvas.convert("RGB")
