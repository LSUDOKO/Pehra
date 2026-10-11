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


LOOSEN_WORDS = (
    "skip", "less strict", "loosen", "remove the break", "no break", "work through", "hata do", "hatao",
    "kam karo", "dheela", "chhod do", "mat do", "nahi chahiye break", "break band",
    "remove the stop", "ignore the plan", "without rest", "without any rest", "no rest", "less rest",
    "work through", "stop window hata", "aaram kam", "bina aaram", "break hata",
)

LOOSEN_REPLY = (
    "Main plan ko dheela nahi kar sakta. Sirf site supervisor Override dabakar, "
    "kam se kam 10 akshar ka kaaran likhkar, plan badal sakta hai. Yeh record mein save hoga.\n"
    "I cannot loosen the plan. Only the supervisor can, by tapping Override and writing a reason."
)


def is_loosen_request(text: str) -> bool:
    t = re.sub(r"\s+", " ", text.lower())
    return any(w in t for w in LOOSEN_WORDS)
