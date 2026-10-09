"""search_guidance: keyword lookup over a small set of vetted, cited passages."""

import functools
import json
import re
from pathlib import Path

_INDEX = Path(__file__).parent / "guidance_index" / "passages.json"


@functools.cache
def _passages() -> list[dict]:
    return json.loads(_INDEX.read_text())


def search_guidance(query: str, k: int = 2) -> list[dict]:
    words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for p in _passages():
        score = len(words & set(p["tags"])) * 3 + len(words & set(re.findall(r"\w+", p["text"].lower())))
        if score:
            scored.append((score, p))
    scored.sort(key=lambda s: -s[0])
    return [{"text": p["text"], "source": p["source"]} for _, p in scored[:k]]
