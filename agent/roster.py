"""Rule-based crew roster parsing: '40 log, 10 bhaari kaam, 3 naye aaye'.

Rules first; the model is only a fallback for odd phrasing. The result is
always read back to the supervisor for confirmation before it is saved.
"""

import re

_ROMAN = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6,
    "chhah": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "barah": 12,
    "baarah": 12, "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16, "satrah": 17,
    "atharah": 18, "unnis": 19, "bees": 20, "pachchis": 25, "pachis": 25, "tees": 30,
    "paintis": 35, "chalis": 40, "chaalis": 40, "paintalis": 45, "pachas": 50, "pachaas": 50,
    "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90, "sau": 100,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
}
_DEVANAGARI = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7,
    "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15,
    "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20, "पच्चीस": 25, "तीस": 30,
    "पैंतीस": 35, "चालीस": 40, "पैंतालीस": 45, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80,
    "नब्बे": 90, "सौ": 100,
}
_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

KEYWORDS = {
    "heavy_count": ("bhaari", "bhari", "heavy", "भारी"),
    "new_count": ("naye", "naya", "nayi", "new", "नए", "नये", "नया"),
    "headcount": ("log", "logo", "mazdoor", "majdoor", "worker", "workers", "aadmi", "लोग",
                  "मज़दूर", "मजदूर", "आदमी", "people"),
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\wऀ-ॿ]+", text.translate(_DIGITS).lower())


def _as_number(tok: str) -> int | None:
    if tok.isdigit():
        return int(tok)
    return _ROMAN.get(tok) or _DEVANAGARI.get(tok)


def _nearest_field(window: list[str]) -> str | None:
    """First keyword after a number, stopping at the next number."""
    for w in window:
        if _as_number(w) is not None:
            return None
        for field, kws in KEYWORDS.items():
            if w in kws:
                return field
    return None


def parse_crew_roster(transcript: str) -> dict:
    """Return {headcount, heavy_count, new_count, confidence, unmatched}."""
    toks = _tokens(transcript)
    out: dict = {"headcount": None, "heavy_count": 0, "new_count": 0}
    unmatched = []
    for i, tok in enumerate(toks):
        n = _as_number(tok)
        if n is None:
            continue
        field = _nearest_field(toks[i + 1:i + 4])
        if field:
            out[field] = n
        else:
            unmatched.append(n)
    if out["headcount"] is None and unmatched:
        out["headcount"] = unmatched.pop(0)
    ok = out["headcount"] is not None and out["heavy_count"] + out["new_count"] <= out["headcount"]
    out["confidence"] = 0.0 if not ok else (1.0 if not unmatched else 0.6)
    out["unmatched"] = unmatched
    return out


def readback(r: dict) -> str:
    return (f"{r['headcount']} log, {r['heavy_count']} bhaari kaam, {r['new_count']} naye. "
            "Sahi hai?")
