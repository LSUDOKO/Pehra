"""Deterministic routing that never depends on the model.

Symptom messages always get the fixed first-aid text, even if Bedrock is up.
"""

import re

SYMPTOM_WORDS = (
    "chakkar", "behosh", "behoshi", "ulti", "sar dard", "sardard", "bukhar", "pasina band",
    "dizzy", "faint", "fainted", "vomit", "collapse", "unconscious", "heat stroke", "heatstroke",
    "चक्कर", "बेहोश", "उल्टी", "सिर दर्द",
)


def is_symptom(text: str) -> bool:
    t = re.sub(r"\s+", " ", text.lower())
    return any(w in t for w in SYMPTOM_WORDS)
