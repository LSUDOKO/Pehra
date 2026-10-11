"""Drawing kit for the demo video: palette, fonts, easing, cached sprites, text tiles and cards."""

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
CHARS = Path("out/video/chars")
FONTS = Path("/usr/share/fonts/noto")

PEACH = (253, 216, 189)
SAND = (255, 236, 218)
CREAM = (255, 248, 240)
INK = (43, 27, 18)
MUTED = (125, 96, 78)
WHITE = (255, 255, 255)
GREEN, YELLOW, ORANGE, RED, PURPLE = (47, 179, 68), (255, 194, 14), (255, 138, 31), (232, 40, 43), (162, 102, 176)
LEVELS = [GREEN, YELLOW, ORANGE, RED, PURPLE]
WATER = (41, 171, 226)
DEEP = (16, 28, 48)
NIGHT = (24, 40, 66)
AWS = (255, 153, 0)
WA_GREEN, WA_DARK, WA_BUBBLE, WA_BG = (37, 211, 102), (7, 94, 84), (220, 248, 198), (236, 229, 221)


# ---------- easing ----------
def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return a if x < a else b if x > b else x


def prog(t: float, a: float, b: float) -> float:
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k


def ease_out(k: float) -> float:
    return 1 - (1 - k) ** 3


def ease_in(k: float) -> float:
    return k ** 3


def ease_in_out(k: float) -> float:
    return 4 * k ** 3 if k < 0.5 else 1 - (-2 * k + 2) ** 3 / 2


def ease_back(k: float, s: float = 1.70158) -> float:
    return 1 + (s + 1) * (k - 1) ** 3 + s * (k - 1) ** 2


def ease_elastic(k: float) -> float:
    if k in (0.0, 1.0):
        return k
    return 2 ** (-10 * k) * math.sin((k * 10 - 0.75) * (2 * math.pi) / 3) + 1


def pop(t: float, a: float, dur: float = 0.5) -> float:
    return ease_back(prog(t, a, a + dur))


def fade(t: float, a: float, dur: float = 0.4, out_at: float | None = None, out_dur: float = 0.3) -> float:
    k = ease_out(prog(t, a, a + dur))
    if out_at is not None:
        k *= 1 - ease_in(prog(t, out_at, out_at + out_dur))
    return k


def mix(c1: tuple, c2: tuple, k: float) -> tuple:
    return tuple(int(round(lerp(a, b, k))) for a, b in zip(c1, c2))


# ---------- fonts and text ----------
@lru_cache(maxsize=64)
def font(size: int, weight: str = "Bold", script: str = "") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"NotoSans{script}-{weight}.ttf"), size)


@lru_cache(maxsize=4096)
def text_tile(s: str, size: int, weight: str, color: tuple, script: str = "", stroke: int = 0,
              stroke_color: tuple | None = None) -> Image.Image:
    f = font(size, weight, script)
    asc, desc = f.getmetrics()
    pad = 4 + stroke
    w = int(math.ceil(f.getlength(s))) + 2 * pad
    im = Image.new("RGBA", (max(w, 1), asc + desc + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad, pad + asc), s, font=f, fill=color + (255,), anchor="ls",
                            stroke_width=stroke, stroke_fill=(stroke_color or color) + (255,))
    return im


def text_w(s: str, size: int, weight: str = "Bold", script: str = "") -> float:
    return font(size, weight, script).getlength(s)


def fit(s: str, size: int, max_w: float, weight: str = "Black") -> int:
    while size > 20 and text_w(s, size, weight) > max_w:
        size -= 2
    return size


def wrap(s: str, size: int, max_w: float, weight: str = "Medium") -> list[str]:
    lines = []
    for para in s.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if cur and text_w(trial, size, weight) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def with_alpha(im: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return out


def paste(canvas: Image.Image, im: Image.Image, x: float, y: float, alpha: float = 1.0) -> None:
    """alpha_composite that clips at the canvas edges."""
    if alpha <= 0.003:
        return
    x, y = int(round(x)), int(round(y))
    cw, ch = canvas.size
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(im.width, cw - x), min(im.height, ch - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    if (sx0, sy0, sx1, sy1) != (0, 0, im.width, im.height):
        im = im.crop((sx0, sy0, sx1, sy1))
    canvas.alpha_composite(with_alpha(im, alpha), (x + sx0, y + sy0))


def text(canvas: Image.Image, s: str, x: float, y: float, size: int = 40, weight: str = "Bold",
         color: tuple = INK, anchor: str = "l", alpha: float = 1.0, scale: float = 1.0, script: str = "",
         stroke: int = 0, stroke_color: tuple | None = None) -> float:
    """Draw text with its top-left (anchor l), top-centre (m) or top-right (r) at x, y. Returns width."""
    tile = text_tile(s, size, weight, color, script, stroke, stroke_color)
    if abs(scale - 1) > 0.01:
        tile = tile.resize((max(1, int(tile.width * scale)), max(1, int(tile.height * scale))), Image.BICUBIC)
    dx = {"l": 0, "m": tile.width / 2, "r": tile.width}[anchor]
    paste(canvas, tile, x - dx, y, alpha)
    return tile.width


# ---------- emoji ----------
@lru_cache(maxsize=64)
def emoji(ch: str, size: int) -> Image.Image:
    f = ImageFont.truetype(str(FONTS / "NotoColorEmoji.ttf"), 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    box = im.getbbox() or (0, 0, 1, 1)
    im = im.crop(box)
    return im.resize((size, max(1, int(im.height * size / im.width))), Image.LANCZOS)


def is_emoji(ch: str) -> bool:
    return ord(ch[0]) > 0x2500


# ---------- shapes ----------
@lru_cache(maxsize=256)
def rrect(w: int, h: int, r: int, fill: tuple, outline: tuple | None = None, width: int = 0) -> Image.Image:
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f = fill if len(fill) == 4 else fill + (255,)
    o = None if outline is None else (outline if len(outline) == 4 else outline + (255,))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=f, outline=o, width=width)
    return im


@lru_cache(maxsize=128)
def soft_shadow(w: int, h: int, r: int, blur: int = 22, strength: int = 70) -> Image.Image:
    m = blur * 2
    im = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((m, m, m + w, m + h), r, fill=(60, 30, 10, strength))
    return im.filter(ImageFilter.GaussianBlur(blur))


def card(canvas: Image.Image, x: float, y: float, w: int, h: int, r: int = 28, fill: tuple = CREAM,
         alpha: float = 1.0, shadow: bool = True, outline: tuple | None = None, width: int = 0) -> None:
    w, h = int(w), int(h)
    if w < 2 or h < 2:
        return
    if shadow:
        sh = soft_shadow(w, h, r)
        paste(canvas, sh, x - (sh.width - w) / 2, y - (sh.height - h) / 2 + 10, alpha)
    paste(canvas, rrect(w, h, r, fill, outline, width), x, y, alpha)


@lru_cache(maxsize=64)
def ellipse_shadow(w: int, strength: int = 80) -> Image.Image:
    h = max(6, w // 7)
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((20, 20, 20 + w, 20 + h), fill=(70, 35, 10, strength))
    return im.filter(ImageFilter.GaussianBlur(9))


@lru_cache(maxsize=64)
def glow(r: int, color: tuple, strength: int = 150) -> Image.Image:
    size = r * 2
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    a = (np.clip(1 - d, 0, 1) ** 2 * strength).astype(np.uint8)
    arr = np.zeros((size, size, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


# ---------- backgrounds ----------
@lru_cache(maxsize=32)
def gradient(top: tuple, bottom: tuple, w: int = W, h: int = H) -> Image.Image:
    k = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - k) + np.array(bottom)[None, None, :] * k)
    arr = np.repeat(arr, w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def shimmer(im: Image.Image, t: float, y0: int, y1: int, amp: float = 4.0) -> Image.Image:
    """Heat haze: shift horizontal bands with a travelling sine."""
    arr = np.array(im)
    for y in range(y0, y1, 3):
        s = int(round(amp * math.sin(y / 23 + t * 5.5) * (y - y0) / max(1, y1 - y0)))
        if s:
            arr[y:y + 3] = np.roll(arr[y:y + 3], s, axis=1)
    return Image.fromarray(arr, "RGBA")


@lru_cache(maxsize=8)
def grain() -> Image.Image:
    rng = np.random.default_rng(7)
    a = rng.integers(0, 14, (H, W), dtype=np.uint8)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA")


# ---------- characters ----------
@lru_cache(maxsize=64)
def pose(name: str) -> Image.Image:
    """A cut-out pose. Poses that carry a piece of scene background get feathered side edges (hides seams)."""
    im = Image.open(CHARS / f"{name}.png").convert("RGBA")
    a = np.asarray(im.getchannel("A"), dtype=np.float32)
    if (a > 20).mean() > 0.5:
        w = a.shape[1]
        ramp = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (w * 0.09), 0, 1)
        top = np.clip(np.arange(a.shape[0]) / (a.shape[0] * 0.05), 0, 1)
        im.putalpha(Image.fromarray((a * ramp[None, :] * top[:, None]).astype(np.uint8)))
    return im


@lru_cache(maxsize=1024)
def pose_sized(name: str, w: int, h: int, rot: int = 0, flip: bool = False) -> Image.Image:
    im = pose(name).resize((w, h), Image.LANCZOS)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rot:
        im = im.rotate(rot / 10, resample=Image.BICUBIC, expand=True)
    return im


def sprite(canvas: Image.Image, name: str, cx: float, base: float, h: float, alpha: float = 1.0,
           rot: float = 0.0, flip: bool = False, shadow: bool = True, sx: float = 1.0, sy: float = 1.0,
           shadow_gap: float = 0.0) -> tuple[float, float, float, float]:
    """Draw a pose with its bottom-centre at (cx, base). Returns the drawn box."""
    src = pose(name)
    hq = max(4, int(round(h * sy / 2) * 2))
    wq = max(4, int(round(src.width * h / src.height * sx / 2) * 2))
    im = pose_sized(name, wq, hq, int(round(rot * 2)) * 5, flip)
    if shadow:
        sh = ellipse_shadow(int(wq * 0.75) // 8 * 8)
        k = 1 / (1 + shadow_gap / 120)
        sh = sh if k > 0.98 else sh.resize((max(8, int(sh.width * k)), max(4, int(sh.height * k))))
        paste(canvas, sh, cx - sh.width / 2, base + shadow_gap - sh.height / 2, alpha * k)
    x, y = cx - im.width / 2, base - im.height
    paste(canvas, im, x, y, alpha)
    return x, y, im.width, im.height


def bob(t: float, speed: float = 1.6, amp: float = 6.0, phase: float = 0.0) -> float:
    return math.sin(t * speed * 2 * math.pi / 2 + phase) * amp


# ---------- chat bubble ----------
def bubble(canvas: Image.Image, x: float, y: float, w: int, body: str, alpha: float = 1.0, size: int = 26,
           fill: tuple = WA_BUBBLE, meta: str = "", max_lines: int = 11) -> int:
    """A WhatsApp-style message bubble. Leading emoji are drawn in colour. Returns its height."""
    pad = 22
    lines = []
    for raw in body.split("\n"):
        lead = ""
        if raw and is_emoji(raw[0]):
            lead, raw = raw[0], raw[1:].lstrip("️ ").lstrip()
        for i, ln in enumerate(wrap(raw, size, w - 2 * pad - (size + 8 if lead else 0), "Regular")):
            lines.append((lead if i == 0 else "", ln, bool(lead)))
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [("", "…", False)]
    lh = int(size * 1.38)
    h = pad * 2 + lh * len(lines) + (lh if meta else 0)
    card(canvas, x, y, w, h, 22, fill, alpha)
    yy = y + pad
    for lead, ln, indent in lines:
        xx = x + pad
        if lead:
            paste(canvas, emoji(lead, size), xx, yy + 4, alpha)
        if indent:
            xx += size + 8
        text(canvas, ln, xx, yy - 2, size, "Regular", INK, alpha=alpha)
        yy += lh
    if meta:
        text(canvas, meta, x + w - pad, yy - 2, int(size * 0.72), "Medium", (110, 130, 110), "r", alpha)
    return h


def pill(canvas: Image.Image, s: str, x: float, y: float, size: int = 28, fill: tuple = INK,
         color: tuple = WHITE, alpha: float = 1.0, anchor: str = "l", weight: str = "Bold") -> int:
    tw = int(text_w(s, size, weight))
    w, h = tw + size * 2, int(size * 1.9)
    x0 = x - {"l": 0, "m": w / 2, "r": w}[anchor]
    paste(canvas, rrect(w, h, h // 2, fill), x0, y, alpha)
    text(canvas, s, x0 + size, y + (h - size * 1.45) / 2 - 2, size, weight, color, alpha=alpha)
    return w
