"""Fixed Hindi (Roman script) texts for personal/family forecasts, water, rain, nights and sensors.

Placeholder discipline as before: every number comes from heatcore outputs.
"""

from heatcore.personal import LEVEL_HI
from heatcore.rain import HINDI as RAIN_HI
from heatcore.templates_hi import clock

LEVEL_ICON = {"kam": "🟢", "saavdhaan": "🟡", "zyada": "🟠", "bahut_zyada": "🔴", "khatarnak": "🟣"}
LEVEL_ACTION = {
    "kam": "Normal din. Paani peete rahiye.",
    "saavdhaan": "Dhoop mein lambe kaam se bachiye. Har ghante paani piyiye.",
    "zyada": "Dopahar ki dhoop se bachiye. Chhaon aur aaram lijiye.",
    "bahut_zyada": "Zaroorat na ho to dopahar mein bahar mat jaiye. Buzurgon aur bachchon ka khaas dhyan rakhiye.",
    "khatarnak": "Bahar ka kaam band rakhiye. Ghar ko thanda rakhiye. Bimar mehsoos ho to 108.",
}
GROUP_HI = {"adults": "Swasth vayask", "vulnerable": "Buzurg, bachche, garbhvati, bimar",
            "outdoor_worker": "Bahar kaam karne wale"}


def span(r) -> str:
    return f"{clock(r[0])} se {clock(r[1])} baje"


def rain_line(rain: dict | None) -> str | None:
    if not rain or not rain.get("alert"):
        return None
    return (f"🌧 {RAIN_HI[rain['category']].capitalize()} ka anuman ({rain['total_mm']} mm). "
            "Paani bharne wali sadkon se bachiye. Bijli ke taar aur naali se door rahiye.")


def site_rain_line(rain: dict | None) -> str | None:
    if not rain or not rain.get("alert"):
        return None
    return (f"- {RAIN_HI[rain['category']].capitalize()} ({rain['total_mm']} mm): khudai, scaffolding aur "
            "bijli ka kaam band. Paani nikasi check karein.")


def night_line(night: dict | None) -> str | None:
    if not night or night.get("warm_night", "none") == "none":
        return None
    kind = "bahut garam raat" if night["warm_night"] == "very_warm" else "garam raat"
    return (f"🌙 Aaj {kind}: raat ka kam se kam taapmaan {night['night_min_c']}°C. Sone se pehle naha lijiye, "
            "khidki khol kar hawa aane dijiye, paani paas rakhiye.")


def site_night_line(night: dict | None) -> str | None:
    if not night or night.get("warm_night", "none") == "none":
        return None
    return (f"- Garam raat ({night['night_min_c']}°C): mazdooron ke rehne ki jagah mein hawa aur paani ka "
            "intezaam karein. Thaka hua sharir agle din zyada khatre mein hota hai.")


def flood_line(flood: dict | None) -> str | None:
    if not flood or not flood.get("alert"):
        return None
    word = "bahut tezi se" if flood["level"] == "severe" else "tezi se"
    return f"🌊 Nadi ka paani {word} badh sakta hai. Nadi ke kinare na jaiye. Sarkari suchna sunte rahiye."


def personal_message(place: str, f: dict, cond: dict, forecast_line: str) -> str:
    lvl = f["overall_level"]
    who = " (ghar ke sabse kamzor sadasya ke liye)" if len(f["groups"]) > 1 else ""
    out = [f"{LEVEL_ICON[lvl]} Aaj {place}{who}: {LEVEL_HI[lvl]}"]
    for g, data in f["groups"].items():
        line = f"- {GROUP_HI[g]}: {LEVEL_HI[data['peak_level']]}"
        if data["avoid"]:
            line += "; bahar na jaiye " + ", ".join(span(r) for r in data["avoid"])
        out.append(line)
    if f["better_windows"]:
        out.append("✅ Bahar ke kaam ke liye behtar samay: " + ", ".join(span(r) for r in f["better_windows"]))
    else:
        out.append("✅ Aaj din mein koi kam-khatre wala samay nahi. Zaroori kaam subah jaldi kariye.")
    out.append(LEVEL_ACTION[lvl])
    for extra in (night_line(cond.get("night")), rain_line(cond.get("rain")), flood_line(cond.get("flood"))):
        if extra:
            out.append(extra)
    out.append("Paani ki jagah dhoondhne ke liye: /paani")
    out.append(forecast_line)
    return "\n".join(out)


def family_call_text(place: str, f: dict) -> str:
    strict = f["groups"].get("vulnerable") or f["groups"]["adults"]
    t = f"Namaste. Yeh Pehra ka sandesh hai. Aaj {place} mein bahut garmi aur nami hai. "
    if strict["avoid"]:
        t += f"{span(strict['avoid'][0])} tak ghar ke andar rahiye. "
    return t + "Thoda thoda paani peete rahiye. Chakkar, uljhan ya behoshi ho to turant 108 par call kariye."


def places_reply(points: list[dict], known: int) -> str:
    if not points:
        return ("Aapke 5 km mein koi paani ya chhaon ki jagah hamare record mein nahi hai "
                f"({known} jagah is shahar mein darj). Aap /add_paani se nayi jagah jod sakte hain.")
    kind = {"drinking_water": "💧 Peene ka paani", "water_point": "💧 Paani", "shelter": "⛱ Chhaon/shelter",
            "community_water": "💧 Paani (logon ne bataya, jaanch nahi hui)"}
    lines = ["Sabse paas:"]
    for p in points:
        name = f" - {p['name']}" if p.get("name") else ""
        lines.append(f"{kind.get(p['kind'], p['kind'])}{name}: {p['distance_m']} m\n{p['link']}")
    lines.append("Data: OpenStreetMap (ODbL) aur log. Jagah badal sakti hai.")
    return "\n".join(lines)


def sensor_hotter_text(cmp: dict) -> str:
    return (f"🌡 Site sensor: WBGT abhi {cmp['measured']}°C, forecast {cmp['forecast']}°C "
            f"({cmp['diff_c']}°C zyada). Site forecast se garam hai (tin ki chhat? concrete?). "
            "Aaram badhaiye, chhaon aur paani paas rakhiye.")


def tank_low_text(pct: int, cans: int | None) -> str:
    extra = f" Aaj ke plan ke hisaab se {cans} bade can chahiye." if cans else ""
    return f"🚰 Paani ki tanki sirf {pct}% bachi hai. Turant bharwaiye.{extra}"


def drain_high_text(level_cm: float) -> str:
    return (f"🌊 Naali/sadak sensor: paani {level_cm} cm tak bhar gaya hai. Raasta band ho sakta hai. "
            "Bijli ke kaam aur gaadi chalana rokiye.")
