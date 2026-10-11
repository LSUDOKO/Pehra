"""Cut each character sheet into transparent poses (flood-fill the flat background, split by gaps).

    uv run python scripts/video/cut_characters.py
Writes out/video/chars/<name>_<i>.png
"""

import glob
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC = Path("Pehra_Character_Sheets")
OUT = Path("out/video/chars")
MARK = (255, 0, 255)
MIN_GAP = 12
MIN_WIDTH = 140
EXPECTED = {"boondi": 4}
# seams left by the neighbouring panel (left, right px)
INSET = {"boondi_4": (48, 0), "dadi_2": (130, 85), "dadi_3": (30, 0), "lakshmi_2": (50, 60), "lakshmi_3": (14, 0)}


def cut(path: Path) -> list[Image.Image]:
    im = Image.open(path).convert("RGB")
    w, h = im.size
    work = im.copy()
    seeds = [(x, 0) for x in range(0, w, 40)] + [(x, h - 1) for x in range(0, w, 40)] + \
            [(0, y) for y in range(0, h, 40)] + [(w - 1, y) for y in range(0, h, 40)]
    for s in seeds:
        if work.getpixel(s) != MARK:
            ImageDraw.floodfill(work, s, MARK, thresh=40)
    arr = np.array(work)
    fg = ~((arr[..., 0] == 255) & (arr[..., 1] == 0) & (arr[..., 2] == 255))
    alpha = Image.fromarray((fg * 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.copy()
    rgba.putalpha(alpha)
    cols = np.array(alpha).max(axis=0) > 20
    segs, start, gap = [], None, 0
    for x, c in enumerate(list(cols) + [False] * MIN_GAP):
        if c:
            start = x if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= MIN_GAP:
                segs.append([start, x - gap + 1])
                start, gap = None, 0
    merged = []
    for s in segs:  # small fragments (icons, sparkles) join the nearest neighbour
        if merged and (s[1] - s[0] < MIN_WIDTH or merged[-1][1] - merged[-1][0] < MIN_WIDTH):
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    expected = EXPECTED.get(path.stem.split("_", 1)[1].lower(), 3)
    if len(merged) < expected:  # poses with scene backgrounds touch: fall back to equal panels
        step = w / expected
        merged = [[int(i * step), int((i + 1) * step)] for i in range(expected)]
    out = []
    for x0, x1 in merged:
        piece = trim_slivers(rgba.crop((max(0, x0 - 6), 0, min(w, x1 + 6), h)))
        bbox = piece.getchannel("A").getbbox()
        out.append(piece.crop(bbox))
    return out


def trim_slivers(piece: Image.Image, share: float = 0.04) -> Image.Image:
    """Clear thin column runs at the panel edges that belong to the neighbouring pose."""
    a = np.array(piece.getchannel("A"))
    mass = (a > 20).sum(axis=0)
    runs, start = [], None
    for x, m in enumerate(list(mass) + [0]):
        if m and start is None:
            start = x
        elif not m and start is not None:
            runs.append((start, x))
            start = None
    total = mass.sum() or 1
    keep = [r for r in runs if mass[r[0]:r[1]].sum() / total >= share or 0 < r[0] and r[1] < len(mass)]
    a2 = np.zeros_like(a)
    for x0, x1 in keep:
        a2[:, x0:x1] = a[:, x0:x1]
    out = piece.copy()
    out.putalpha(Image.fromarray(a2))
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(glob.glob(str(SRC / "*.png"))):
        name = Path(f).stem.split("_", 1)[1].lower()
        poses = cut(Path(f))
        for i, p in enumerate(poses, 1):
            left, right = INSET.get(f"{name}_{i}", (0, 0))
            p = p.crop((left, 0, p.width - right, p.height))
            p.crop(p.getchannel("A").getbbox()).save(OUT / f"{name}_{i}.png")
        print(f"{name:18s} {len(poses)} poses  {[p.size for p in poses]}")
