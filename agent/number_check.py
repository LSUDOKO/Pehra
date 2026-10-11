"""Every number the AI says must appear in a tool output from the same turn.

Unmatched numbers -> regenerate once with the list -> else fixed template.
"""

import json
import re

NUM_RE = re.compile(r"(?<![\w.])(\d{1,4}(?:[.:]\d{1,2})?)(?![\w])")
LIST_MARKER_RE = re.compile(r"^\s*\d{1,2}[.)]\s", re.MULTILINE)
ALWAYS_ALLOWED = {"108"}  # national ambulance number in the fixed first-aid text


def canon(token: str) -> str:
    """'06' -> '6', '28.20' -> '28.2', '6:00' -> '6', '6:30' -> '6:30'."""
    if ":" in token:
        h, m = token.split(":")
        return str(int(h)) if int(m) == 0 else f"{int(h)}:{int(m):02d}"
    f = float(token)
    return str(int(f)) if f == int(f) else f"{f:g}"


def numbers_in_text(text: str) -> list[str]:
    text = LIST_MARKER_RE.sub(" ", text)
    return [canon(t) for t in NUM_RE.findall(text)]


def allowed_numbers(tool_outputs: list) -> set[str]:
    """Numbers in tool outputs, plus spoken forms: 12h clock and percentages."""
    raw = re.findall(r"\d+(?:\.\d+)?", json.dumps(tool_outputs, default=str))
    out = set(ALWAYS_ALLOWED)
    for r in raw:
        c = canon(r)
        out.add(c)
        f = float(r)
        if f == int(f) and 0 <= f <= 24:
            h = int(f) % 12
            out.add(str(12 if h == 0 else h))
        if 0 < f < 1:
            out.add(canon(str(round(f * 100, 1))))
    return out


def verify_numbers(reply_text: str, tool_outputs: list) -> list[str]:
    """Return the numbers in the reply that no tool produced (empty list = pass)."""
    allowed = allowed_numbers(tool_outputs)
    unmatched = {n for n in numbers_in_text(reply_text) if n not in allowed}
    return sorted(unmatched | set(verify_units(reply_text, tool_outputs)))


# Unit-aware checks: a number written next to a unit must equal that unit's tool value.
# Catches "9 can" when build_water_plan said 7 even though 9 exists elsewhere (an hour).
UNIT_RULES = (
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:bade\s+|big\s+|paani\s+ke\s+)?(?:can|cans|कैन)\b", re.I), "cans_20l"),
    (re.compile(r"(\d+(?:\.\d+)?)\s*(?:litre|liter|litres|liters|लीटर)\b", re.I), "litres"),
)
NEUTRAL_UNIT_VALUES = {"20"}  # "20 litre" describes the can size, not the order


def _tool_values(tool_outputs: list, key: str) -> set[str]:
    found = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == key and isinstance(v, (int, float)):
                    found.add(canon(str(v)))
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(tool_outputs)
    return found


def verify_units(reply_text: str, tool_outputs: list) -> list[str]:
    """Numbers attached to a unit that disagree with that unit's tool value (only if the tool ran)."""
    bad = []
    for rx, key in UNIT_RULES:
        expected = _tool_values(tool_outputs, key)
        if not expected:
            continue
        for m in rx.finditer(reply_text):
            n = canon(m.group(1))
            if n not in expected and n not in NEUTRAL_UNIT_VALUES:
                bad.append(n)
    return sorted(set(bad))
