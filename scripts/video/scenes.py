"""The demo video's scenes. Each renderer draws one frame: render(t, d, cue) -> RGBA image.

Every number comes from docs/results/ and every chat bubble is produced by the project's own code
(heatcore templates) from the Kharghar ERA5 day or cached OpenStreetMap points.
"""

import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from kit import (
    AWS,
    CREAM,
    DEEP,
    FPS,
    GREEN,
    INK,
    MUTED,
    NIGHT,
    ORANGE,
    PEACH,
    PURPLE,
    RED,
    SAND,
    WA_BG,
    WA_BUBBLE,
    WA_DARK,
    WA_GREEN,
    WATER,
    WHITE,
    YELLOW,
    H,
    W,
    bob,
    bubble,
    card,
    clamp,
    ease_back,
    ease_in,
    ease_in_out,
    ease_out,
    emoji,
    fade,
    fit,
    glow,
    gradient,
    lerp,
    mix,
    paste,
    pill,
    pop,
    pose,
    prog,
    rrect,
    shimmer,
    sprite,
    text,
    text_w,
    wrap,
)
from PIL import Image, ImageDraw

from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.personal import Household, personal_forecast
from heatcore.places import map_link, nearest
from heatcore.plan import HourHeat
from heatcore.templates_hi import render_plan_hi, render_symptom_alert_hi
from heatcore.templates_people import family_call_text, personal_message, places_reply

RESULTS = Path("docs/results")
IMG = Path("docs/img")
VID = Path("out/video")


class Cue:
    """Word timings of a scene's voice-over, in scene-local seconds."""

    def __init__(self, words: list[tuple[float, str]], lead: float, vo_dur: float):
        self.words, self.lead, self.vo_dur = words, lead, vo_dur

    def at(self, word: str, default: float, n: int = 0) -> float:
        hits = [t for t, w in self.words if w.lower().strip(".,!?'\"").startswith(word.lower())]
        return self.lead + hits[n] if len(hits) > n else default

    @property
    def end(self) -> float:
        return self.lead + self.vo_dur


@dataclass
class Scene:
    key: str
    vo: str
    min_dur: float
    render: Callable
    accent: tuple = ORANGE
    lang: str = "en-IN"
    label: str = ""
    overlays: list = field(default_factory=list)  # (clip_key, box, t0, t1) in scene-local time; t1 None = end
    extra_audio: list = field(default_factory=list)  # (scene-local start, audio file, volume)
    dur: float = 0.0
    start: float = 0.0
    cue: Cue | None = None


# ---------- data ----------
@lru_cache(maxsize=1)
def kharghar() -> dict:
    return json.loads((RESULTS / "kharghar_replay.json").read_text())


@lru_cache(maxsize=1)
def audit() -> dict:
    return json.loads((RESULTS / "audit_summary.json").read_text())


def _heat() -> list[HourHeat]:
    day = datetime(2023, 4, 16)
    return [HourHeat(day + timedelta(hours=h["hour"]), h["wbgt_sun"], h["wbgt_shade"]) for h in kharghar()["hours"]]


def _plan(site_type: str, name: str) -> dict:
    return build_daily_plan(_heat(), Crew(headcount=40), ForecastMeta("ERA5 reanalysis", datetime(2023, 4, 15, 12)),
                            datetime(2023, 4, 15, 19), site_id="demo", site_name=name, site_type=site_type)


FC_LINE = "Forecast: ERA5 reanalysis, 16 Apr 07:00 IST."


def excerpt(msg: str, starts: tuple) -> str:
    """Keep the lines that start with these prefixes, marking skipped lines with an ellipsis."""
    out, skipped = [], False
    for ln in msg.split("\n"):
        if ln.startswith(starts):
            if skipped:
                out.append("…")
            out.append(ln)
            skipped = False
        else:
            skipped = True
    return "\n".join(out)


@lru_cache(maxsize=1)
def bot() -> dict:
    """Real bot texts from the project's templates, for the Kharghar day (16 Apr 2023)."""
    k = kharghar()
    family = personal_forecast(_heat(), Household(adults=2, young_children=1, pregnant=1))
    elder = personal_forecast(_heat(), Household(adults=1, elderly=1))
    d = json.loads(Path("out/places/delhi.json").read_text()) if Path("out/places/delhi.json").exists() else []
    pts = d["points"] if isinstance(d, dict) else d
    near = nearest(pts, 28.6315, 77.2167, k=2)
    for p in near:
        p["link"] = map_link(p["lat"], p["lon"])
    return {
        "site": render_plan_hi(k["plan"]),
        "rider": excerpt(render_plan_hi(_plan("rider", "Arjun, Kharghar")), ("Kal", "- Kaam band", "- 2 se", "- Delivery",
                                                                              "- Paani")),
        "school": excerpt(render_plan_hi(_plan("school", "School, Kharghar")), ("Kal", "- Kaam band", "- 10 se",
                                                                                "- School", "- Paani")),
        "family": personal_message("Kharghar", family, {"rain": None, "night": None, "flood": None}, FC_LINE),
        "call": family_call_text("Kharghar", elder),
        "water": places_reply(near, len(pts)) if near else "Sabse paas:\n💧 Peene ka paani: 250 m",
        "symptom": render_symptom_alert_hi("13:20", 2),
        "plan": k["plan"],
    }


# ---------- shared chrome ----------
def corner_label(c: Image.Image, s: str, t: float, dark: bool = False) -> None:
    if s:
        pill(c, s, W - 48, 40, 20, (255, 255, 255) if dark else INK, INK if dark else WHITE,
             fade(t, 0.5) * 0.92, "r", "Bold")


def brand_mark(c: Image.Image, t: float, dark: bool = False) -> None:
    col = WHITE if dark else INK
    a = fade(t, 0.4) * 0.85
    text(c, "PEHRA", 52, 34, 30, "Black", col, alpha=a)
    text(c, "पहरा", 52 + text_w("PEHRA", 30, "Black") + 12, 30, 28, "Bold", ORANGE, alpha=a, script="Devanagari")


def shake(t: float, at: float, amp: float = 10, dur: float = 0.35) -> tuple[float, float]:
    k = prog(t, at, at + dur)
    if k <= 0 or k >= 1:
        return 0.0, 0.0
    e = (1 - k) * amp
    return math.sin(t * 90) * e, math.cos(t * 77) * e


# ---------- 1. cold open ----------
def s_cold(t: float, d: float, cue: Cue) -> Image.Image:
    c = gradient((255, 190, 130), PEACH).copy()
    pulse = 1 + 0.04 * math.sin(t * 2.2)
    g = glow(int(560 * pulse), (255, 150, 40), 170)
    paste(c, g, 1500 - g.width / 2, 250 - g.height / 2)
    paste(c, rrect(W, 300, 0, (246, 196, 158)), 0, 800)
    t_thermo = cue.at("thermometer", 1.6)
    t_inv = cue.at("heat", 4.6) - 0.1
    t_meet = cue.at("meet", 6.5)
    # Garmi strolls in
    k = ease_out(prog(t, 0.2, 1.8))
    gx = lerp(2250, 1500, k) + 900 * ease_in(prog(t, t_meet - 0.5, t_meet + 0.3))
    sprite(c, "garmi_1", gx, 900 + bob(t, 1.4, 8), 560, rot=math.sin(t * 3) * 2 * (1 - k * 0.6))
    # thermometer card
    a = fade(t, t_thermo - 0.3)
    s = lerp(0.85, 1, pop(t, t_thermo - 0.3))
    cx, cy = 430, 540
    cw, ch = int(520 * s), int(330 * s)
    card(c, cx - cw / 2, cy - ch / 2, cw, ch, 36, CREAM, a)
    if s > 0.97:
        text(c, "THERMOMETER", cx, cy - 130, 26, "Bold", MUTED, "m", a)
        text(c, "38.8 °C", cx, cy - 92, 110, "Black", INK, "m", a)
        k2 = fade(t, t_thermo + 0.6)
        pill(c, "no heatwave alert", cx, cy + 70, 30, GREEN, WHITE, a * k2, "m")
    # title slam
    if t >= t_inv - 0.15:
        dx, dy = shake(t, t_inv + 0.2)
        k = ease_out(prog(t, t_inv - 0.15, t_inv + 0.2))
        sc = lerp(1.7, 1.0, k)
        ghost = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 3.1))
        text(c, "INVISIBLE", W / 2 + dx, 110 + dy, 168, "Black", WHITE, "m", k * ghost, sc, stroke=4,
             stroke_color=INK)
        text(c, "HEAT", W / 2 + dx, 300 + dy, 168, "Black", RED, "m", k, sc)
    c = shimmer(c, t, 560, 1080, 5)
    # Boondi and the Pehra mark
    if t >= t_meet - 0.2:
        k = pop(t, t_meet - 0.2, 0.6)
        sprite(c, "boondi_1", 1010, 960 + bob(t, 1.8, 7), 360 * k, shadow=k > 0.5)
        a = fade(t, t_meet)
        lx = 1230 + lerp(80, 0, ease_out(prog(t, t_meet, t_meet + 0.5)))
        text(c, "PEHRA", lx, 600, 130, "Black", INK, alpha=a)
        text(c, "पहरा", lx + text_w("PEHRA", 130, "Black") + 26, 596, 108, "Bold", ORANGE, alpha=a,
             script="Devanagari")
        text(c, "a heat & water guard on WhatsApp", lx + 6, 770, 36, "Medium", INK, alpha=fade(t, t_meet + 0.4))
    return c


# ---------- 2. Kharghar ----------
CH_X, CH_Y, CH_W, CH_H = 820, 120, 1020, 790


def s_kharghar(t: float, d: float, cue: Cue) -> Image.Image:
    k = kharghar()
    c = gradient(SAND, (250, 222, 196)).copy()
    brand_mark(c, t)
    # left column
    a = fade(t, 0.3)
    x = 110
    text(c, "16 APRIL 2023", x + lerp(-60, 0, ease_out(prog(t, 0.3, 0.9))), 120, 74, "Black", INK, alpha=a)
    text(c, "Kharghar, Navi Mumbai · open-air event", x, 214, 32, "Bold", MUTED, alpha=fade(t, 0.6))
    t_temp = cue.at("temperature", 3.5)
    tiles = [
        (f"{k['imd']['tmax_c']} °C", "max temperature that day", ORANGE, t_temp),
        (f"+{k['imd']['departure_c']} °C", "above the 1991–2020 normal", ORANGE, t_temp + 0.7),
    ]
    for i, (big, small, col, ta) in enumerate(tiles):
        y = 300 + i * 175
        kk = ease_back(prog(t, ta, ta + 0.5))
        aa = fade(t, ta, 0.3)
        card(c, x + lerp(-40, 0, kk), y, 600, 150, 28, CREAM, aa)
        text(c, big, x + 36 + lerp(-40, 0, kk), y + 14, 74, "Black", col, alpha=aa)
        text(c, small, x + 36 + lerp(-40, 0, kk), y + 104, 26, "Medium", MUTED, alpha=aa)
    t_alarm = cue.at("alarm", t_temp + 2.0)
    if t >= t_alarm - 0.1:
        kk = prog(t, t_alarm - 0.1, t_alarm + 0.25)
        sc = lerp(1.8, 1.0, ease_out(kk))
        stamp = stamp_tile("NO HEATWAVE ALERT", "IMD rule, recreated", GREEN)
        st = stamp.resize((int(stamp.width * sc), int(stamp.height * sc)))
        paste(c, st, x + 300 - st.width / 2, 735 - st.height / 2, ease_out(kk))
    # chart
    t_chart = cue.at("but", 6.0)
    ca = fade(t, t_chart - 0.6)
    card(c, CH_X, CH_Y + lerp(40, 0, ease_out(prog(t, t_chart - 0.6, t_chart))), CH_W, CH_H, 36, CREAM, ca)
    if ca > 0.01:
        chart(c, t, ca, cue, t_chart)
    kg = ease_in_out(prog(t, t_chart - 0.9, t_chart - 0.1))
    gx, gy, gh = lerp(1330, CH_X + CH_W - 40, kg), lerp(820, CH_Y + 70, kg), lerp(560, 230, kg)
    sprite(c, "garmi_2", gx, gy + bob(t, 1.2, 6), gh * fade(t, 1.0), shadow=False)
    return c


@lru_cache(maxsize=4)
def stamp_tile(big: str, small: str, col: tuple) -> Image.Image:
    w, h = 560, 170
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    paste(im, rrect(w, h, 22, (255, 255, 255, 0), col, 7), 0, 0)
    text(im, big, w / 2, 24, 50, "Black", col, "m")
    text(im, small, w / 2, 100, 28, "Bold", col, "m")
    return im.rotate(-7, resample=Image.BICUBIC, expand=True)


def chart(c: Image.Image, t: float, a: float, cue: Cue, t0: float) -> None:
    k = kharghar()
    hours = [h for h in k["hours"] if 6 <= h["hour"] <= 19]
    lim = k["limits"]["moderate"]["rel_c"]
    x0, y0 = CH_X + 110, CH_Y + 650           # plot origin (bottom-left)
    pw, ph = CH_W - 170, 470
    vmin, vmax = 20.0, 34.0
    vy = lambda v: y0 - (v - vmin) / (vmax - vmin) * ph  # noqa: E731
    text(c, "WBGT in the sun, hour by hour (°C)", CH_X + 50, CH_Y + 34, 34, "Bold", INK, alpha=a)
    text(c, "heat + humidity + sun + wind, the number that harms the body", CH_X + 50, CH_Y + 82, 24,
         "Medium", MUTED, alpha=a)
    n = len(hours)
    bw = pw / n
    # event window
    ev = [i for i, h in enumerate(hours) if 10 <= h["hour"] < 14]
    ea = a * fade(t, t0 + 0.4) * 0.9
    paste(c, rrect(int(bw * len(ev)), ph + 30, 12, (232, 40, 43, 34)), x0 + ev[0] * bw, y0 - ph - 20, ea)
    text(c, "event, late morning", x0 + (ev[0] + len(ev) / 2) * bw, y0 - ph - 18, 22, "Bold", RED, "m", ea)
    for v in (22, 26, 30):
        text(c, f"{v}", x0 - 18, vy(v) - 16, 22, "Medium", MUTED, "r", a)
    t_bars = cue.at("heat", t0 + 0.8, 1)
    for i, h in enumerate(hours):
        kb = ease_back(prog(t, t_bars + i * 0.09, t_bars + i * 0.09 + 0.55), 1.2)
        v = vmin + (h["wbgt_sun"] - vmin) * kb
        top = vy(v)
        over = h["wbgt_sun"] > lim and kb > 0.95
        col = RED if over else (250, 176, 110)
        bh = int(y0 - top)
        if bh > 2:
            paste(c, rrect(int(bw - 14), bh, 8, col), x0 + i * bw + 7, top, a)
        if i % 2 == 0:
            text(c, f"{h['hour']}:00", x0 + i * bw + bw / 2, y0 + 10, 20, "Medium", MUTED, "m", a)
    t_lim = cue.at("limit", t_bars + 1.4)
    la = a * fade(t, t_lim - 0.3)
    ly = vy(lim)
    kx = ease_out(prog(t, t_lim - 0.3, t_lim + 0.4))
    for xx in range(int(x0), int(x0 + pw * kx), 26):
        paste(c, rrect(16, 5, 2, INK), xx, ly - 2, la)
    pill(c, f"{lim} °C · NIOSH limit, moderate work", x0 + 6, ly - 60, 22, INK, WHITE, la, "l")
    pk = max(hours, key=lambda h: h["wbgt_sun"])
    pi = hours.index(pk)
    pa = a * fade(t, t_lim + 1.0)
    pill(c, f"peak {pk['wbgt_sun']} °C at {pk['hour']}:00", x0 + pi * bw + bw / 2, vy(pk["wbgt_sun"]) - 64, 22, RED,
         WHITE, pa, "m")
    text(c, "ERA5 reanalysis via Open-Meteo (CC BY 4.0) · our calculation · IMD rule recreated, not an official record",
         CH_X + 50, CH_Y + CH_H - 50, 19, "Medium", MUTED, alpha=a)


# ---------- 3. audit ----------
def s_audit(t: float, d: float, cue: Cue) -> Image.Image:
    a_ = audit()
    tot = a_["total"]
    c = gradient(NIGHT, DEEP).copy()
    brand_mark(c, t, dark=True)
    t_n = cue.at("4,372", 2.2)
    k = ease_out(prog(t, t_n - 0.4, t_n + 1.6))
    n = int(round(tot["invisible_days_shade"] * k))
    text(c, f"{n:,}", 110, 170, 230, "Black", mix(YELLOW, ORANGE, k), alpha=fade(t, t_n - 0.4))
    text(c, "invisible heat days", 120, 440, 58, "Black", WHITE, alpha=fade(t, t_n))
    text(c, "WBGT above the work limit, no heatwave declared", 122, 520, 28, "Medium", (200, 210, 225),
         alpha=fade(t, t_n + 0.3))
    text(c, "12 cities · 2021–2025 · shade, 06–19 IST", 122, 562, 28, "Medium", (200, 210, 225),
         alpha=fade(t, t_n + 0.5))
    chips = [(f"{tot['invisible_shade_outside_mar_jun']:,} outside March–June", ORANGE, cue.at("half", t_n + 3)),
             (f"{tot['heavy_rain_days']} heavy-rain days", WATER, cue.at("heavy", t_n + 5)),
             (f"{tot['warm_nights']} warm nights", PURPLE, cue.at("warm", t_n + 6))]
    for i, (s, col, ta) in enumerate(chips):
        kk = pop(t, ta - 0.2, 0.5)
        if kk > 0:
            pill(c, s, 120, 650 + i * 92, int(32 * clamp(kk, 0.5, 1.2)), col, WHITE if col != YELLOW else INK, clamp(kk))
    # city bars
    rows = sorted(a_["districts"], key=lambda r: -r["invisible_days_shade"])
    mx = rows[0]["invisible_days_shade"]
    bx, by, bmax = 1240, 150, 520
    text(c, "invisible heat days per city", bx - 260, by - 70, 26, "Bold", (200, 210, 225), alpha=fade(t, 0.8))
    for i, r in enumerate(rows):
        y = by + i * 60
        kb = ease_out(prog(t, 0.9 + i * 0.12, 1.9 + i * 0.12))
        aa = fade(t, 0.8 + i * 0.12)
        name = r["city"].split(",")[0]
        text(c, name, bx - 24, y + 4, 26, "Bold", WHITE, "r", aa)
        v = r["invisible_days_shade"]
        bw = max(6, int(bmax * v / mx * kb))
        col = mix(YELLOW, RED, v / mx)
        paste(c, rrect(bw, 38, 10, col), bx, y + 6, aa)
        text(c, f"{int(v * kb)}", bx + bw + 14, y + 6, 26, "Bold", (230, 236, 245), alpha=aa)
    text(c, "A minimum: ERA5 (~25 km) smooths humid extremes. IMD rule recreated per city.", 120, 940 - 36, 22,
         "Medium", (160, 172, 190), alpha=fade(t, 2.0))
    return c


# ---------- 4. people ----------
@dataclass
class Person:
    key: str
    name: str
    role: str
    feature: str
    poses: tuple
    tint: tuple
    accent: tuple
    extra: Callable
    boondi: str | None = None


def v_bubble(kind: str, meta: str = "Pehra · 7:00 pm", max_lines: int = 10):
    def draw(c, t, d, x, y, w):
        hdr(c, t, x, y)
        bubble(c, x, y + 70 + lerp(30, 0, ease_out(prog(t, 0.7, 1.2))), w, bot()[kind], fade(t, 0.7), 25,
               WHITE, meta, max_lines)
    return draw


def hdr(c, t, x, y):
    a = fade(t, 0.5)
    paste(c, rrect(44, 44, 22, WA_GREEN), x, y, a)
    text(c, "P", x + 22, y + 2, 28, "Black", WHITE, "m", a)
    text(c, "Pehra", x + 58, y - 2, 28, "Bold", INK, alpha=a)
    text(c, "WhatsApp · Hindi", x + 58, y + 30, 18, "Medium", MUTED, alpha=a)


def x_ramesh(c, t, d, x, y, w):
    v_bubble("site", "7:00 pm", 9)(c, t, d, x, y, w)
    ka = fade(t, 1.8)
    yy = y + 470
    paste(c, rrect(w, 74, 37, WA_BUBBLE), x, yy, ka)
    paste(c, rrect(46, 46, 23, WA_DARK), x + 16, yy + 14, ka)
    ImageDraw.Draw(c)  # noqa: B018
    tri = Image.new("RGBA", (46, 46), (0, 0, 0, 0))
    ImageDraw.Draw(tri).polygon([(17, 12), (17, 34), (35, 23)], fill=WHITE + (255,))
    paste(c, tri, x + 16, yy + 14, ka)
    for i in range(34):
        hh = 8 + 26 * abs(math.sin(i * 1.7 + t * 6 * (t > 2.2)))
        paste(c, rrect(6, int(hh), 3, WA_DARK), x + 82 + i * 11, yy + 37 - hh / 2, ka)
    text(c, "0:24 Hindi voice note", x + w - 24, yy + 20, 22, "Bold", WA_DARK, "r", ka)
    kb = pop(t, 2.6)
    for i, s in enumerate(("Approve", "Override")):
        bw = (w - 16) // 2
        paste(c, rrect(bw, 64, 18, WHITE), x + i * (bw + 16), yy + 92, clamp(kb))
        text(c, s, x + i * (bw + 16) + bw / 2, yy + 102, 26, "Bold", (0, 140, 125), "m", clamp(kb))
    if t > 3.4:
        r = 30 + 60 * prog(t, 3.4, 3.9)
        paste(c, glow(int(r), WA_GREEN, int(200 * (1 - prog(t, 3.4, 3.9)))), x + (w - 16) // 4 - r, yy + 124 - r)


@lru_cache(maxsize=2)
def worker_page(h: int) -> Image.Image:
    im = Image.open(IMG / "worker-page.png").convert("RGBA")
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 26, fill=255)
    im.putalpha(m)
    return im


def x_gurpreet(c, t, d, x, y, w):
    ph = worker_page(540)
    k = ease_out(prog(t, 0.5, 1.1))
    a = fade(t, 0.5)
    px = x
    card(c, px - 14, y + 30 - 14 + lerp(40, 0, k), ph.width + 28, ph.height + 28, 40, INK, a)
    paste(c, ph, px, y + 30 + lerp(40, 0, k), a)
    bx = px + ph.width + 50
    ta = d * 0.5
    text(c, "supervisor gets, if he taps 'chakkar':", bx, y + 120, 22, "Bold", MUTED, alpha=fade(t, ta))
    bubble(c, bx, y + 160 + lerp(30, 0, ease_out(prog(t, ta, ta + 0.5))), w - ph.width - 50,
           bot()["symptom"], fade(t, ta), 24, (255, 236, 236), "now")


def x_bhanwari(c, t, d, x, y, w):
    plan = bot()["plan"]["plans"]["moderate"]["hours"]
    hrs = [h for h in plan if 6 <= h["hour"] <= 18]
    sw = (w - 120) / len(hrs)
    stops = [i for i, h in enumerate(hrs) if h["status"] == "stop"]
    cols = {0: (205, 232, 210), 15: YELLOW, 30: ORANGE, 45: RED}
    for i, h in enumerate(hrs):
        k = ease_back(prog(t, 0.7 + i * 0.07, 1.2 + i * 0.07))
        stop = h["status"] == "stop"
        col = PURPLE if stop else cols.get(h["rest_minutes"], RED)
        bh = int(220 * k)
        if bh > 4:
            paste(c, rrect(int(sw - 8), bh, 12, col), x + i * sw + 4, y + 300 - bh)
        a = fade(t, 0.9 + i * 0.07)
        if h["rest_minutes"] and not stop and k > 0.9:
            text(c, f"{h['rest_minutes']}'", x + i * sw + sw / 2, y + 300 - 44, 24, "Black",
                 INK if col == YELLOW else WHITE, "m", a)
        text(c, f"{h['hour'] % 12 or 12}", x + i * sw + sw / 2, y + 312, 22, "Bold", MUTED, "m", a)
    if stops:
        sa = fade(t, 0.9 + stops[-1] * 0.07)
        pill(c, "STOP WORK", x + (stops[0] + len(stops) / 2) * sw, y + 30, 22, PURPLE, WHITE, sa, "m")
    la = fade(t, 2.0)
    items = [("work", (205, 232, 210)), ("15' rest / hour", YELLOW), ("30'", ORANGE), ("45'", RED),
             ("stop work", PURPLE)]
    xx = x
    for s, col in items:
        paste(c, rrect(26, 26, 8, col), xx, y + 390, la)
        xx += 36 + text(c, s, xx + 34, y + 384, 22, "Bold", INK, alpha=la) + 18
    text(c, "Kharghar, 16 Apr 2023: the plan Pehra would have sent", x, y + 450, 26, "Bold", MUTED, alpha=fade(t, 2.4))
    sprite(c, "garmi_1", x + w - 50, y + 300 + bob(t, 1.3, 5), 200 * fade(t, 1.6))


def x_lakshmi(c, t, d, x, y, w):
    hdr(c, t, x, y)
    me = 0.8
    k = ease_out(prog(t, me, me + 0.4))
    bw = 200
    paste(c, rrect(bw, 70, 22, WA_BUBBLE), x + w - bw, y + 74 + lerp(20, 0, k), fade(t, me))
    text(c, "paani kahan?", x + w - bw / 2, y + 90 + lerp(20, 0, k), 26, "Bold", INK, "m", fade(t, me))
    paste(c, rrect(bw, 70, 22, WA_BUBBLE), x + w - bw, y + 160, fade(t, me + 0.4))
    paste(c, emoji("📍", 28), x + w - bw + 34, y + 180, fade(t, me + 0.4))
    text(c, "location", x + w - bw / 2 + 22, y + 176, 26, "Bold", INK, "m", fade(t, me + 0.4))
    ta = me + 1.1
    bubble(c, x, y + 250 + lerp(30, 0, ease_out(prog(t, ta, ta + 0.5))), w, bot()["water"], fade(t, ta), 24,
           WHITE, "OpenStreetMap · Delhi")


def x_dadi(c, t, d, x, y, w):
    tc = d * 0.42
    a = 1 - prog(t, tc, tc + 0.3)
    if a > 0:
        cw, ch = 420, 470
        cx = x + 40
        card(c, cx, y, cw, ch, 40, (24, 36, 52), a * fade(t, 0.4))
        for i in range(3):
            ph = (t * 1.2 + i / 3) % 1
            r = int(60 + ph * 90)
            paste(c, glow(r, WA_GREEN, int(120 * (1 - ph))), cx + cw / 2 - r, y + 170 - r, a)
        paste(c, rrect(120, 120, 60, WA_GREEN), cx + cw / 2 - 60, y + 110, a)
        text(c, "P", cx + cw / 2, y + 130, 64, "Black", WHITE, "m", a)
        text(c, "Pehra alert", cx + cw / 2, y + 260, 36, "Black", WHITE, "m", a)
        text(c, "incoming call · Hindi", cx + cw / 2, y + 310, 24, "Medium", (190, 200, 210), "m", a)
        paste(c, rrect(150, 64, 32, WA_GREEN), cx + cw / 2 - 75, y + 370, a)
        text(c, "answer", cx + cw / 2, y + 380, 26, "Bold", WHITE, "m", a)
    if t > tc:
        hdr(c, t - tc, x, y)
        bubble(c, x, y + 70 + lerp(30, 0, ease_out(prog(t, tc + 0.2, tc + 0.7))), w, "📞 " + bot()["call"],
               fade(t, tc + 0.2), 26, WHITE, "Hindi voice · Amazon Polly")


EXTRAS = {"ramesh": x_ramesh, "gurpreet": x_gurpreet, "bhanwari": x_bhanwari, "lakshmi": x_lakshmi, "dadi": x_dadi}

PEOPLE = [
    Person("ramesh", "RAMESH", "site supervisor · Navi Mumbai", "Tomorrow's plan at 7 pm, in Hindi",
           ("ramesh_2", "ramesh_3"), (255, 226, 196), ORANGE, x_ramesh),
    Person("gurpreet", "GURPREET", "construction worker", "Scan the site QR. No app, no login",
           ("gurpreet_1", "gurpreet_3"), (214, 232, 248), WATER, x_gurpreet),
    Person("bhanwari", "BHANWARI", "brick-kiln worker", "Rest before the heat peaks",
           ("bhanwari_1", "bhanwari_3"), (255, 214, 200), RED, x_bhanwari),
    Person("arjun", "ARJUN", "delivery rider", "Break windows built for riders",
           ("arjun_1", "arjun_3"), (255, 238, 190), YELLOW, v_bubble("rider", "7:00 pm", 9), "boondi_2"),
    Person("lakshmi", "LAKSHMI", "street vendor · Delhi", "\"Paani kahan?\" Nearest drinking water",
           ("lakshmi_2", "lakshmi_3"), (208, 236, 246), WATER, x_lakshmi, "boondi_3"),
    Person("dadi", "DADI", "grandmother", "A Hindi phone call on dangerous days",
           ("dadi_2", "dadi_1"), (234, 220, 244), PURPLE, x_dadi),
    Person("meena", "MEENA & CHOTU", "mother-to-be and her son", "Stricter limits for children and pregnancy",
           ("meena_and_chotu_1", "meena_and_chotu_2"), (214, 240, 214), GREEN, v_bubble("family", "7:00 am", 10)),
    Person("fernandes", "MS FERNANDES", "school principal", "School mode: assembly indoors",
           ("ms_fernandes_1", "ms_fernandes_2"), (220, 228, 250), (70, 110, 200), v_bubble("school", "7:00 pm", 10),
           "boondi_4"),
]


def make_person(p: Person) -> Callable:
    def render(t: float, d: float, cue: Cue) -> Image.Image:
        c = gradient(mix(p.tint, WHITE, 0.35), p.tint).copy()
        brand_mark(c, t)
        r = int(400 + 12 * math.sin(t * 2))
        paste(c, glow(r, WHITE, 200), 520 - r, 520 - r)
        swap = d * 0.52
        a1 = 1 - prog(t, swap - 0.12, swap + 0.12)
        k1 = ease_out(prog(t, 0.0, 0.6))
        base = 910
        h = 700
        if a1 > 0:
            sprite(c, p.poses[0], lerp(-300, 520, k1), base, h * lerp(1, 0.96, 1 - a1), alpha=a1,
                   sy=1 + 0.012 * math.sin(t * 5))
        if t > swap - 0.12:
            k2 = pop(t, swap - 0.12, 0.45)
            sprite(c, p.poses[1], 520, base, h * lerp(0.9, 1, k2), alpha=clamp(k2), sy=1 + 0.012 * math.sin(t * 5))
        # text column
        x = 1010
        k = ease_out(prog(t, 0.2, 0.7))
        pill(c, p.name, x + lerp(60, 0, k), 120, 28, p.accent, WHITE if p.accent != YELLOW else INK, fade(t, 0.2))
        text(c, p.role, x + lerp(60, 0, k), 190, 26, "Bold", MUTED, alpha=fade(t, 0.3))
        text(c, p.feature, x + lerp(60, 0, k), 232, fit(p.feature, 44, 860), "Black", INK, alpha=fade(t, 0.35))
        p.extra(c, t, d, x, 330, 700 if p.boondi else 780)
        if p.boondi:
            kb = pop(t, 1.4, 0.6)
            sprite(c, p.boondi, 1815, 940 + bob(t, 1.8, 6), 200 * kb, shadow=False, flip=p.boondi == "boondi_3")
        corner_label(c, "illustrated characters · real bot text", t)
        return c
    return render


# ---------- 5. Site Box ----------
WOKWI_BOX = (80, 170, 900, 740)
TWIN_BOX = (1030, 170, 810, 456)

PARTS = [("DHT22", "air temperature + humidity", ORANGE),
         ("Black globe", "DS18B20 inside: the sun's radiant heat", INK),
         ("= site WBGT", "measured on the spot, every 10 s", RED),
         ("2 × sonar", "drinking-water tank + drain level", WATER),
         ("Siren + LED ring", "rest bell every hour, colour = risk", PURPLE),
         ("Relays", "mist fan on, tank pump on", GREEN),
         ("SOS button", "phone call + WhatsApp to supervisor", RED)]


@lru_cache(maxsize=2)
def still(name: str, w: int, h: int) -> Image.Image | None:
    for p in ([VID / "wokwi_still.png", Path(".playwright-mcp/sitebox-wokwi.png"), IMG / "wokwi-esp32.png"]
              if name == "wokwi" else [VID / "twin_still.png", IMG / "twin.png"]):
        if p.exists():
            im = Image.open(p).convert("RGBA")
            if p.name == "sitebox-wokwi.png":
                im = im.crop((800, 80, 1600, 800))
            elif p.name == "wokwi_still.png":
                im = im.crop((0, 0, im.width, int(im.height * 0.78)))  # serial monitor shows a device token
            im.thumbnail((w, h), Image.LANCZOS)
            return im
    return None


def panel(c, box, t, a, kind, live_clip: bool, label: str):
    x, y, w, h = box
    card(c, x - 10, y - 10, w + 20, h + 20, 26, (30, 44, 66), a)
    if not live_clip:
        im = still(kind, w, h)
        if im is not None:
            z = 1 + 0.04 * t / 25
            im2 = im.resize((int(im.width * z), int(im.height * z)))
            im2 = im2.crop(((im2.width - im.width) // 2, (im2.height - im.height) // 2,
                            (im2.width + im.width) // 2, (im2.height + im.height) // 2))
            paste(c, im2, x + (w - im.width) / 2, y + (h - im.height) / 2, a)
    pill(c, label, x + 14, y + h - 58, 18, (12, 20, 34), WHITE, a * 0.9)


def make_sitebox(clips: set) -> Callable:
    def render(t: float, d: float, cue: Cue) -> Image.Image:
        c = gradient(NIGHT, DEEP).copy()
        brand_mark(c, t, dark=True)
        text(c, "Pehra Site Box", 80, 84, 52, "Black", WHITE, alpha=fade(t, 0.2))
        text(c, "₹600 of parts · ESP32 · for sites without smartphones", 80 + text_w("Pehra Site Box", 52, "Black") + 30,
             104, 26, "Medium", (190, 200, 215), alpha=fade(t, 0.4))
        corner_label(c, "SIMULATED HARDWARE · WOKWI", t, dark=True)
        panel(c, WOKWI_BOX, t, fade(t, 0.3), "wokwi", "wokwi" in clips, "Wokwi ESP32 simulator · real firmware")
        t_twin = cue.at("live", d * 0.62)
        # parts list (before the twin)
        la = 1 - prog(t, t_twin - 0.6, t_twin - 0.2)
        if la > 0:
            x, y = 1050, 190
            for i, (a_, b_, col) in enumerate(PARTS):
                ta = 1.0 + i * (t_twin - 2.5) / len(PARTS)
                k = ease_out(prog(t, ta, ta + 0.4))
                aa = fade(t, ta) * la
                yy = y + i * 98
                paste(c, rrect(16, 70, 8, col if col != INK else (60, 70, 90)), x + lerp(40, 0, k), yy, aa)
                text(c, a_, x + 36 + lerp(40, 0, k), yy - 4, 34, "Black", WHITE, alpha=aa)
                text(c, b_, x + 36 + lerp(40, 0, k), yy + 40, 24, "Medium", (190, 200, 215), alpha=aa)
        if t > t_twin - 0.4:
            a = fade(t, t_twin - 0.4)
            panel(c, TWIN_BOX, t, a, "twin", "twin" in clips, "live 3D twin · Three.js · polls the box state")
            flow(c, t, t_twin, a)
        return c
    return render


def flow(c, t, t0, a):
    steps = ["Site Box", "AWS IoT Core", "Lambda + Cedar", "siren · fan · pump", "WhatsApp + call"]
    x0, y, w = 1110, 690, 650
    gap = w / (len(steps) - 1)
    for i in range(len(steps) - 1):
        paste(c, rrect(int(gap), 6, 3, (70, 90, 120)), x0 + i * gap, y + 27, a)
    ph = ((t - t0) / 2.2) % 1
    px = x0 + ph * w
    paste(c, glow(26, AWS, 255), px - 26, y + 30 - 26, a)
    for i, s in enumerate(steps):
        on = abs(px - (x0 + i * gap)) < 40
        r = 22 if on else 16
        paste(c, rrect(2 * r, 2 * r, r, AWS if on else (110, 130, 160)), x0 + i * gap - r, y + 30 - r, a)
        text(c, s, x0 + i * gap, y + 68 + (i % 2) * 40, 22, "Bold", WHITE, "m", a)


# ---------- 6. AWS ----------
COLS = [110, 560, 1010, 1460]
ROWS = [210, 420, 630, 840 - 30]
NODES = {
    "meteo": (0, 0, "Open-Meteo", "free forecast", (120, 130, 150)),
    "sched": (1, 0, "EventBridge", "Scheduler, 3× a day", (230, 70, 140)),
    "wbgt": (2, 0, "Lambda", "WBGT once per city", AWS),
    "s3": (3, 0, "S3", "heat store", GREEN),
    "wa": (0, 1, "WhatsApp", "Cloud API webhook", WA_GREEN),
    "api": (1, 1, "API Gateway", "HTTP API", (160, 90, 220)),
    "botfn": (2, 1, "Lambda", "bot + plans", AWS),
    "sfn": (3, 1, "Step Functions", "waits for Approve", (230, 70, 140)),
    "sqs": (0, 2, "SQS + DLQ", "rate-limited sending", (230, 70, 140)),
    "polly": (1, 2, "Polly", "Hindi voice + call audio", (40, 160, 200)),
    "cedar": (2, 2, "Cedar", "policy: never loosen", RED),
    "bedrock": (3, 2, "Bedrock", "Nova Pro + Strands", (40, 160, 160)),
    "iot": (0, 3, "IoT Core", "MQTT, X.509", (60, 150, 90)),
    "boxfn": (1, 3, "Lambda", "Site Box state", AWS),
    "ddb": (2, 3, "DynamoDB", "sites, people, boxes", (60, 100, 210)),
    "lock": (3, 3, "S3 Object Lock", "hash-chained records", GREEN),
}
EDGES = [("meteo", "sched"), ("sched", "wbgt"), ("wbgt", "s3"),
         ("wa", "api"), ("api", "botfn"), ("botfn", "sfn"), ("sfn", "bedrock"), ("bedrock", "cedar"),
         ("cedar", "polly"), ("polly", "sqs"), ("sqs", "wa"),
         ("iot", "boxfn"), ("boxfn", "ddb"), ("ddb", "lock")]
NW, NH = 360, 112


def node_xy(k: str) -> tuple[float, float]:
    col, row = NODES[k][:2]
    return COLS[col], ROWS[row]


def anchor(k: str, other: str) -> tuple[float, float]:
    (x, y), (ox, oy) = node_xy(k), node_xy(other)
    if oy == y:
        return (x + NW, y + NH / 2) if ox > x else (x, y + NH / 2)
    return (x + NW / 2, y + NH) if oy > y else (x + NW / 2, y)


def s_aws(t: float, d: float, cue: Cue) -> Image.Image:
    c = gradient((14, 24, 42), (8, 14, 28)).copy()
    grid = grid_tile()
    paste(c, grid, 0, 0, 0.5)
    text(c, "How AWS runs it", 110, 60, 56, "Black", WHITE, alpha=fade(t, 0.2))
    pill(c, "serverless · ap-south-1 Mumbai · SAM", 110 + text_w("How AWS runs it", 56, "Black") + 30, 72, 22, AWS,
         INK, fade(t, 0.5))
    rows_t = [cue.at("forecast", 1.5), cue.at("step", 6.0), cue.at("bedrock", 9.0), cue.at("record", d - 5)]
    rows_t[3] = min(rows_t[3], d - 3.0)
    row_of = {k: v[1] for k, v in NODES.items()}
    labels = ["FORECAST TO WBGT", "PEOPLE: PLAN, APPROVE, SEND", "AI EXPLAINS, POLICY GUARDS, VOICE", "DEVICES + RECORDS"]
    for r, lab in enumerate(labels):
        text(c, lab, COLS[0] + NW / 2 + 24, ROWS[r] - 36, 20, "Bold", (130, 150, 180), alpha=fade(t, rows_t[r] - 0.6))
    # edges
    for i, (a_, b_) in enumerate(EDGES):
        ta = rows_t[row_of[b_]] + 0.25 * i % 1.2
        k = ease_in_out(prog(t, ta - 0.3, ta + 0.3))
        if k <= 0:
            continue
        (x1, y1), (x2, y2) = anchor(a_, b_), anchor(b_, a_)
        line(c, x1, y1, lerp(x1, x2, k), lerp(y1, y2, k), (90, 110, 145))
    for k_, (col, row, name, sub, colr) in NODES.items():
        ta = rows_t[row] - 0.5 + col * 0.15
        kk = pop(t, ta, 0.45)
        if kk <= 0:
            continue
        x, y = COLS[col], ROWS[row]
        sw, sh = int(NW * clamp(kk, 0.6, 1.1)), int(NH * clamp(kk, 0.6, 1.1))
        card(c, x + (NW - sw) / 2, y + (NH - sh) / 2, sw, sh, 22, (28, 42, 66), clamp(kk), True,
             colr if k_ in ("cedar",) else None, 3)
        if kk > 0.9:
            paste(c, rrect(64, 64, 16, colr), x + 22, y + 24)
            text(c, name[:2] if name != "Lambda" else "λ", x + 54, y + 30, 30, "Black", WHITE if colr != AWS else INK,
                 "m")
            text(c, name, x + 104, y + 18, 30, "Black", WHITE)
            text(c, sub, x + 104, y + 62, 21, "Medium", (175, 188, 210))
    # packets per row
    paths = [["meteo", "sched", "wbgt", "s3"], ["wa", "api", "botfn", "sfn"],
             ["sfn", "bedrock", "cedar", "polly", "sqs", "wa"], ["iot", "boxfn", "ddb", "lock"]]
    for r, path in enumerate(paths):
        t0 = rows_t[r] + 0.6
        if t > t0:
            packet(c, path, (t - t0) / (1.1 * (len(path) - 1)) % 1.3, AWS if r != 3 else (120, 220, 140))
    # "one city = one calculation"
    tm = cue.at("million", rows_t[0] + 2)
    ka = fade(t, tm - 0.2, out_at=tm + 3.2)
    pill(c, "1 city = 1 calculation, shared by every site", COLS[2] + NW / 2, ROWS[0] - 52, 20, YELLOW, INK, ka, "m")
    # Cedar blocks the AI loosening a plan
    tc = cue.at("cedar", rows_t[2] + 3)
    if t > tc - 0.3:
        cedar_block(c, t, tc)
    return c


@lru_cache(maxsize=1)
def grid_tile() -> Image.Image:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for x in range(0, W, 60):
        dr.line((x, 0, x, H), fill=(40, 60, 90, 60))
    for y in range(0, H, 60):
        dr.line((0, y, W, y), fill=(40, 60, 90, 60))
    return im


def line(c, x1, y1, x2, y2, col, wdt=5):
    x0, y0 = min(x1, x2), min(y1, y2)
    w, h = int(abs(x2 - x1)) + wdt, int(abs(y2 - y1)) + wdt
    if w < 1 or h < 1:
        return
    paste(c, rrect(max(w, wdt), max(h, wdt), wdt // 2, col), x0 - wdt / 2, y0 - wdt / 2)


def packet(c, path, k, col):
    if k > 1:
        return
    segs = len(path) - 1
    s = min(int(k * segs), segs - 1)
    f = k * segs - s
    (x1, y1), (x2, y2) = anchor(path[s], path[s + 1]), anchor(path[s + 1], path[s])
    x, y = lerp(x1, x2, f), lerp(y1, y2, f)
    g = glow(30, col, 255)
    paste(c, g, x - 30, y - 30)
    paste(c, rrect(16, 16, 8, WHITE), x - 8, y - 8)


def cedar_block(c, t, tc):
    (bx, by), (cx, _) = anchor("bedrock", "cedar"), anchor("cedar", "bedrock")
    k = prog(t, tc - 0.3, tc + 0.5)
    hit = k >= 1
    x = lerp(bx, cx + 10, ease_in(k)) if not hit else cx + 10 + 70 * ease_out(prog(t, tc + 0.5, tc + 0.9))
    a = 1 - prog(t, tc + 2.6, tc + 3.0)
    if a <= 0:
        return
    pill(c, "AI: loosen the limit?", x, by - 70, 20, RED, WHITE, a, "m")
    paste(c, glow(26, RED, 255), x - 26, by - 26, a)
    if hit:
        kk = pop(t, tc + 0.5, 0.4)
        sx, sy = node_xy("cedar")
        text(c, "DENY", sx + NW / 2, sy - 74, int(44 * clamp(kk, 0.3, 1.2)), "Black", RED, "m", a * clamp(kk))
        r = int(80 + 60 * prog(t, tc + 0.5, tc + 1.1))
        paste(c, glow(r, RED, int(160 * (1 - prog(t, tc + 0.5, tc + 1.1)))), sx + NW / 2 - r, sy + NH / 2 - r)


# ---------- 7. WhatsApp on the phone ----------
PHONE = (560, 66, 430, 880)          # bezel box
SCREEN = (578, 132, 394, 796)        # where the phone recording goes


def chat_script() -> list[tuple[float, str, str]]:
    b = bot()
    return [(0.6, "me", "hi"),
            (1.4, "bot", "Namaste! Aap kiske liye istemal karenge?\n[Site / school / dukaan]  [Mere aur parivar ke liye]"),
            (3.2, "me", "Mere aur parivar ke liye"),
            (4.4, "bot", b["family"]),
            (8.0, "me", "paani"),
            (9.0, "bot", b["water"]),
            (12.5, "me", "/family_call +91 62306 •••••"),
            (13.4, "bot", "Call alert chalu. Khatre ke din Hindi call aayegi.")]


def make_phone(has_clip: bool) -> Callable:
    def render(t: float, d: float, cue: Cue) -> Image.Image:
        c = gradient((255, 214, 186), (250, 196, 160)).copy()
        brand_mark(c, t)
        x, y, w, h = PHONE
        k = ease_out(prog(t, 0, 0.7))
        oy = lerp(120, 0, k)
        card(c, x, y + oy, w, h, 60, (20, 20, 24), fade(t, 0))
        sx, sy, sw, sh = SCREEN
        paste(c, rrect(sw, sh, 30, WA_BG if not has_clip else (0, 0, 0)), sx, sy + oy)
        if not has_clip:
            chat(c, t, sx, sy + oy, sw, sh)
        text(c, "Live on WhatsApp", 1090, 180, 66, "Black", INK, alpha=fade(t, 0.3))
        for i, s in enumerate(("in Hindi, text + voice notes", "phone calls for alerts", "no app to install")):
            ta = 0.8 + i * 0.5
            paste(c, rrect(14, 14, 7, WA_DARK), 1094, 300 + i * 64 + 14, fade(t, ta))
            text(c, s, 1124, 296 + i * 64, 34, "Bold", INK, alpha=fade(t, ta))
        sprite(c, "ramesh_1", 1330, 960 + bob(t, 1.2, 3), 470, alpha=fade(t, 1.6))
        sprite(c, "boondi_2", 1700, 960 + bob(t, 1.8, 7), 300 * pop(t, 2.2, 0.6), shadow=False)
        corner_label(c, "WhatsApp test number · Twilio trial call" if has_clip else "recreated from real bot replies",
                     t)
        return c
    return render


def chat(c, t, x, y, w, h):
    top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    paste(top, rrect(w, 80, 0, WA_DARK), 0, 0)
    text(top, "Pehra", 70, 12, 28, "Bold", WHITE)
    text(top, "online", 70, 46, 18, "Medium", (200, 230, 220))
    paste(top, rrect(40, 40, 20, WA_GREEN), 18, 20)
    msgs = [m for m in chat_script() if m[0] <= t]
    body = Image.new("RGBA", (w, 2400), (0, 0, 0, 0))
    yy = 10
    for ta, who, s in msgs:
        bw = w - 70 if who == "bot" else min(w - 70, int(text_w(s, 20, "Regular")) + 50)
        bx = 12 if who == "bot" else w - bw - 12
        hh = bubble(body, bx, yy, bw, s, fade(t, ta, 0.25), 18, WHITE if who == "bot" else WA_BUBBLE, max_lines=14)
        yy += hh + 14
    view = h - 90
    off = max(0, yy - view)
    paste(top, body.crop((0, off, w, off + view)), 0, 86)
    if t > 13.0:
        a = fade(t, 13.0)
        paste(top, rrect(w - 30, 130, 24, (24, 36, 52)), 15, 100, a)
        text(top, "Pehra alert · calling…", w / 2, 122, 24, "Bold", WHITE, "m", a)
        text(top, "Hindi voice call", w / 2, 160, 18, "Medium", (190, 200, 210), "m", a)
    paste(c, top, x, y)



# ---------- 7b. WhatsApp chapters from the real phone recording ----------
WA_BEZEL = (132, 40, 414, 884)
WA_SCREEN = (150, 62, 378, 840)    # 720x1600 phone recording, scaled to fit

WA = [  # key, title, bullets, pose, voice-over
    ("wa_hi", "Say hi on WhatsApp", ["No app to install: Pehra is a WhatsApp number",
                                     "Choose: site, school, shop, or me and my family"], "meena_and_chotu_1",
     "Here it is on a real phone. A family says hi to Pehra on WhatsApp, and taps: for me and my family."),
    ("wa_profile", "Five taps build the family profile", ["Elderly, under-5s, pregnancy, illness, outdoor work",
                                                          "Counts only, never names"], "meena_and_chotu_2",
     "Five quick button questions build the household: an elderly parent, a small child, a pregnancy, and someone "
     "who works outdoors. Only counts, never names."),
    ("wa_today", "Today's plan for Mumbai, in Hindi", ["From this morning's Open-Meteo forecast",
                                                        "Khatarnak: vulnerable people indoors 9 to 5",
                                                        "Best hours for errands, and 108 if unwell"], "dadi_2",
     "Today's plan arrives in seconds, from this morning's forecast for Mumbai. It is dangerous for the vulnerable "
     "from nine to five, and it lists the best hours for errands."),
    ("wa_paani", "\"paani Connaught Place\"", ["Nearest drinking water: 190 m, with a map link",
                                              "OpenStreetMap points plus community reports",
                                              "Send a location pin or type a landmark"], "lakshmi_3",
     "Paani, Connaught Place. The nearest drinking water is 190 metres away, from OpenStreetMap, with a map link."),
    ("wa_register", "A supervisor registers a site", ["/register Ramesh Tower, Kharghar",
                                                       "Construction, school, shop or delivery rider"], "ramesh_2",
     "Now the supervisor. Ramesh registers his site in Kharghar and picks construction."),
    ("wa_crew", "The crew, in plain Hindi", ["\"40 log, 10 bhaari kaam, 3 naye aaye\"", "Read back before saving",
                                             "/call_on: Hindi call alerts to this phone"], "ramesh_2",
     "He types his crew in plain Hindi: forty people, ten on heavy work, three new. Pehra reads it back before "
     "saving, and he turns on Hindi call alerts."),
    ("wa_plan", "Tomorrow's plan + a Hindi voice note", ["Stop work 9 to 5, rest bands around it",
                                                          "Heavy work stopped, new workers at 20%",
                                                          "7 water cans · Approve or Override"], "ramesh_1",
     "He asks for tomorrow's plan. Stop work from nine to five, rest every hour around it, heavy work stopped, new "
     "workers at twenty percent, and seven water cans. Then the same plan as a Hindi voice note."),
    ("wa_links", "Worker QR page + printable poster", ["One link per site, printed as a QR code",
                                                        "Workers need no app and no login"], "gurpreet_1",
     "Links gives the worker QR page and a printable poster for the site."),
    ("wa_worker", "A worker taps \"chakkar\"", ["Aaram shuru logs a rest break",
                                              "Chakkar aa raha hai shows fixed first aid",
                                              "The supervisor is told at once"], "gurpreet_3",
     "A worker scans the QR. No app, no login. He logs a rest break, then taps chakkar: I feel dizzy. He gets fixed "
     "first aid, and the supervisor is told at once."),
    ("wa_alert", "The supervisor's alert", ["When, and how many reports in the last hour",
                                            "First aid and 108: fixed text, never AI"], "ramesh_1",
     "The supervisor sees when it was pressed, with first aid and 108."),
    ("wa_call", "A Hindi phone call", ["Amazon Polly Hindi voice, played by Twilio",
                                       "Trial account: a short notice plays first",
                                       "You hear the exact audio the call played"], "ramesh_1",
     "And his phone rings with a Hindi call. On this Twilio trial, a short notice plays first. Then the message."),
    ("wa_agent", "Ask anything", ["\"Kya hum kal dopahar 2 baje concrete daal sakte hain?\"",
                                  "Bedrock (Nova Pro) + Strands, answers from tools",
                                  "A number check blocks invented numbers"], "ramesh_3",
     "He asks: can we pour concrete at two tomorrow afternoon? Amazon Bedrock answers from the plan's own tools: "
     "no, heavy work is stopped then."),
    ("wa_family", "Dadi gets a call on dangerous days", ["/family_call adds an elder's number (blurred here)",
                                                          "Today is khatarnak, so one Hindi call goes out",
                                                          "Stay inside 9 to 5, sip water, 108"], "dadi_1",
     "Meena adds Dadi's number for family calls. Today is dangerous, so Dadi gets one Hindi call, telling her to "
     "stay inside from nine to five."),
    ("wa_box", "The Site Box joins from WhatsApp", ["/device box: box id, device token, 3D twin link",
                                                     "Readings over AWS IoT Core (here from a laptop script)",
                                                     "Alerts: hotter than forecast, tank low, pump on"], "boondi_3",
     "The Site Box joins from WhatsApp too. Its readings arrive over AWS IoT Core: the site is hotter than the "
     "forecast, and the water tank is low, so the pump starts."),
    ("wa_twin", "The live 3D twin, on the phone", ["Measured WBGT 34.2 °C: khatarnak, kaam band",
                                                    "Tank refilling, mist fan on",
                                                    "Updates every 3 s from the box state"], "boondi_4",
     "Every box has a live 3D twin. Measured WBGT is thirty four degrees, so work stops. Watch the tank refill."),
    ("wa_sos", "SOS from the site", ["The red SOS button on the box",
                                     "The twin turns red, WhatsApp alert, Hindi call"], "boondi_1",
     "A worker presses the red SOS button. The twin turns red, the supervisor gets a WhatsApp alert, and a Hindi "
     "call."),
    ("wa_override", "Only the supervisor can loosen a plan", ["Override, Dheela, and a written reason",
                                                               "Cedar policy: never the AI",
                                                               "The reason is saved to the record"], "ramesh_3",
     "Only the supervisor can loosen a plan, and only with a written reason. Cedar enforces it, and the reason "
     "goes on the record."),
]


def make_wa(i: int, n: int, title: str, bullets: list, pose_name: str, speed: float, beats: list) -> Callable:
    def render(t: float, d: float, cue: Cue) -> Image.Image:
        c = gradient((222, 245, 228), (200, 232, 214)).copy()
        x, y, w, h = WA_BEZEL
        card(c, x, y, w, h, 56, (16, 16, 20), 1.0)
        sx, sy, sw, sh = WA_SCREEN
        paste(c, rrect(sw, sh, 26, (0, 0, 0)), sx, sy)
        k = ease_out(prog(t, 0.1, 0.6))
        tx = 640 + lerp(60, 0, k)
        pill(c, f"WHATSAPP · REAL PHONE · {i}/{n}", tx, 110, 22, WA_DARK, WHITE, fade(t, 0.1))
        text(c, title, tx, 180, fit(title, 58, 1180), "Black", INK, alpha=fade(t, 0.2))
        yy = 290
        for j, b in enumerate(bullets):
            a = fade(t, 0.5 + j * 0.35)
            paste(c, rrect(16, 16, 8, WA_GREEN), tx + 4, yy + 18, a)
            for ln in wrap(b, 34, 980, "Bold"):
                text(c, ln, tx + 34, yy, 34, "Bold", INK, alpha=a)
                yy += 48
            yy += 18
        if speed > 1:
            pill(c, f"waits shown at {speed:g}× speed", sx + sw - 8, sy + sh + 8, 18, INK, WHITE, 0.85, "r")
        seen = [b for b in beats if b["at"] + 0.4 <= t]
        if beats:
            by = max(yy + 10, 600)
            text(c, "ON THE PHONE NOW", tx, by, 20, "Bold", MUTED, alpha=fade(t, 0.6))
            for j, b in enumerate(seen[-4:]):
                now = b is seen[-1]
                a = fade(t, b["at"] + 0.4, 0.3) * (1.0 if now else 0.55)
                yb = by + 40 + j * 54
                paste(c, rrect(12, 12, 6, WA_GREEN if now else MUTED), tx + 4, yb + 14, a)
                text(c, b["text"], tx + 30, yb, 32 if now else 28, "Bold" if now else "Medium", INK, alpha=a)
        sprite(c, pose_name, 1660, 950 + bob(t, 1.3, 3), 400 * fade(t, 0.6), shadow=True)
        corner_label(c, "real phone recording · WhatsApp test number · Twilio trial", t)
        return c
    return render


def s_phone_intro(t: float, d: float, cue: Cue) -> Image.Image:
    c = gradient((222, 245, 228), (196, 230, 210)).copy()
    brand_mark(c, t)
    k = ease_out(prog(t, 0.2, 0.9))
    text(c, "Live on WhatsApp", 140 + lerp(-60, 0, k), 210, 110, "Black", INK, alpha=fade(t, 0.2))
    text(c, "recorded on a real phone (moto g34, Android 15) on 11 October 2026", 146, 360, 34, "Medium", MUTED,
         alpha=fade(t, 0.6))
    for j, s_ in enumerate(("in Hindi: text, voice notes and phone calls", "families, supervisors, workers, sites",
                            "no app to install")):
        a = fade(t, 1.0 + j * 0.4)
        paste(c, rrect(16, 16, 8, WA_DARK), 150, 470 + j * 70 + 18, a)
        text(c, s_, 180, 466 + j * 70, 38, "Bold", INK, alpha=a)
    sprite(c, "ramesh_1", 1350, 960 + bob(t, 1.2, 3), 560, alpha=fade(t, 0.8))
    sprite(c, "boondi_2", 1700, 960 + bob(t, 1.8, 7), 330 * pop(t, 1.4, 0.6), shadow=False)
    sprite(c, "dadi_1", 1000, 980, 420, alpha=fade(t, 1.1))
    return c

# ---------- 8. outro ----------
LINEUP = ["ms_fernandes_2", "dadi_2", "gurpreet_2", "ramesh_3", "bhanwari_2"]


def s_outro(t: float, d: float, cue: Cue) -> Image.Image:
    c = gradient((255, 206, 160), (253, 226, 204)).copy()
    r = 420
    paste(c, glow(r, WHITE, 180), W / 2 - r, 470 - r)
    sprite(c, "garmi_3", lerp(1650, 2100, ease_in(prog(t, d - 3, d))), 290 + bob(t, 0.9, 6), 260, shadow=False)
    text(c, "Stay cool, India.", W / 2, 100, 104, "Black", INK, "m", fade(t, 0.3), lerp(1.2, 1, ease_out(prog(t, 0.3, 0.8))))
    for i, name in enumerate(LINEUP):
        ta = 0.6 + i * 0.14
        kk = pop(t, ta, 0.55)
        if kk <= 0:
            continue
        cx = 360 + i * 300
        sprite(c, name, cx, 930 + bob(t, 1.3, 4, i), 470 * kk, sy=1 + 0.01 * math.sin(t * 4 + i))
    kb = pop(t, 1.5, 0.6)
    sprite(c, "boondi_2", 960 + 150, 940 + bob(t, 1.8, 8), 260 * kb, shadow=kb > 0.5)
    a = fade(t, 2.2)
    text(c, "PEHRA", W / 2 - 60, 250, 84, "Black", INK, "r", a)
    text(c, "पहरा", W / 2 - 30, 248, 76, "Bold", ORANGE, "l", a, script="Devanagari")
    text(c, "making invisible heat visible, and acting on it", W / 2, 360, 34, "Medium", INK, "m", fade(t, 2.6))
    ea = fade(t, d - 4.0)
    pill(c, "github.com/LSUDOKO/Pehra · Built on AWS · Team Mavricks", W / 2, 1000 - 30, 24, INK, WHITE, ea, "m")
    return c


# ---------- timeline ----------
VO = {
    "cold": "Every summer, India warns its people with a thermometer. But the heat that hurts is invisible. "
            "Meet Pehra.",
    "kharghar": "On the sixteenth of April, 2023, people died of heatstroke at an open-air event in Kharghar, "
                "near Mumbai. The temperature was 38.8 degrees, so no heatwave alarm was raised. "
                "But heat and humidity together, measured as WBGT, stayed above the safe work limit in the sun, "
                "from ten in the morning to four in the afternoon.",
    "audit": "So we audited twelve Indian cities over five years. 4,372 days crossed the WBGT limit with no "
             "heatwave declared, more than half of them outside the heatwave season. And on the water side: "
             "90 heavy rain days, and 68 warm nights.",
    "ramesh": "Ramesh, a site supervisor, gets tomorrow's plan at 7 pm as a Hindi voice note. "
              "When to stop work, how much rest, how much water. He approves it with one tap.",
    "gurpreet": "Gurpreet scans the site QR code to see the rest plan, and taps chakkar if he feels dizzy. "
                "No app, no login.",
    "bhanwari": "Bhanwari's crew rests in the shade before the heat peaks, not after someone collapses.",
    "arjun": "Arjun, a delivery rider, gets break windows built for riders.",
    "lakshmi": "Lakshmi asks, paani kahan? and finds the nearest drinking water.",
    "dadi": "On dangerous days, Dadi gets a phone call in Hindi, telling her to stay inside.",
    "meena": "Meena's family plan uses stricter limits for her son and her pregnancy.",
    "fernandes": "And Ms Fernandes moves the school assembly indoors.",
    "sitebox": "For sites without smartphones, a six hundred rupee Pehra Site Box measures real WBGT with a "
               "black globe sensor. It rings a rest siren, runs mist fans, refills the water tank, watches the "
               "drain, and has an SOS button. It talks to AWS IoT Core, and every site gets a live 3D twin.",
    "aws": "Under the hood, it is all serverless on AWS. The forecast becomes WBGT once per city, so a million "
           "sites cost the same as one. Step Functions waits for the supervisor's approval. Amazon Bedrock with "
           "Strands explains the plan, but tools do the maths, and Cedar makes sure the AI can never loosen a "
           "safety limit. Every day's record is locked in S3.",
    "phone": "And it lives where people already are. WhatsApp, in Hindi, with voice notes and phone calls. "
             "No app to install.",
    "outro": "Pehra. Making invisible heat visible, and acting on it. Stay cool, India.",
}


def timeline(clips: dict) -> list[Scene]:
    """clips: {'wokwi': (path, w, h, dur), 'twin': ..., 'phone_<chapter>': ...} for the footage that exists."""
    have = set(clips)
    sc = [Scene("cold", VO["cold"], 10.5, s_cold, ORANGE),
          Scene("kharghar", VO["kharghar"], 20.0, s_kharghar, RED),
          Scene("audit", VO["audit"], 15.5, s_audit, (40, 60, 100))]
    for p in PEOPLE:
        sc.append(Scene(p.key, VO[p.key], 5.4, make_person(p), p.accent))
    box = Scene("sitebox", VO["sitebox"], 22.0, make_sitebox(have), WATER)
    if "wokwi" in have:
        box.overlays.append(("wokwi", WOKWI_BOX, 0.3, None))
    sc.append(box)
    chapters = [ch for ch in WA if f"phone_{ch[0]}" in have]
    if chapters:
        sc.append(Scene("phone", VO["phone"], 9.0, s_phone_intro, WA_GREEN))
        for i, (key, title, bullets, pose_name, vo) in enumerate(chapters, 1):
            path, cw, ch_, cdur, meta = clips[f"phone_{key}"]
            s_ = Scene(key, vo, cdur + 1.0, make_wa(i, len(chapters), title, bullets, pose_name, meta["speed"],
                                                    meta.get("beats", [])), WA_GREEN)
            s_.overlays.append((f"phone_{key}", WA_SCREEN, 0.4, None))
            s_.extra_audio = ([(0.4, path, 1.0)] if meta["audio"] else []) + \
                [(0.4 + c_["at"], c_["audio"], 0.9) for c_ in meta["calls"]]
            sc.append(s_)
    else:
        sc.append(Scene("phone", VO["phone"], 16.0, make_phone(False), WA_GREEN))
    sc.append(Scene("aws", VO["aws"], 23.0, s_aws, AWS))
    sc.append(Scene("outro", VO["outro"], 10.0, s_outro, ORANGE))
    return sc


def twin_overlay(scene: Scene) -> None:
    """Called once the twin's start time is known (it follows the VO)."""
    t0 = scene.cue.at("live", scene.dur * 0.62) - 0.2
    scene.overlays.append(("twin", TWIN_BOX, t0, None))


__all__ = ["FPS", "Scene", "Cue", "timeline", "twin_overlay", "WOKWI_BOX", "TWIN_BOX", "SCREEN", "WA", "pose"]
