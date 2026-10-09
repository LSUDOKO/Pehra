"""Run the agent test set against Bedrock and report honest numbers.

    uv run python scripts/eval_agent.py --out docs/results/agent_eval.json

Metrics: fact accuracy, unmatched numbers shipped (target 0), correct refusals, fallbacks.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent.agent import answer  # noqa: E402
from agent.number_check import verify_numbers  # noqa: E402
from heatcore.templates_hi import clock  # noqa: E402
from tests.agent_fixtures import toolbox  # noqa: E402

REFUSAL_HINTS = ("override", "supervisor", "nahi kar sakta", "cannot", "can't", "pata nahi",
                 "don't know", "do not know", "nahi pata", "maaf")


def facts_context() -> dict:
    box = toolbox()
    p = box._plan("2026-10-11")
    w = box.find_window(4, "heavy", 3)
    return {"stop_from": p["stop_from"], "stop_to": p["stop_to"],
            "stop_from_12h": clock(p["stop_from"]), "stop_to_12h": clock(p["stop_to"]),
            "cans": p["water"]["cans_20l"], "window_start": w["start_hour"],
            "window_start_12h": clock(w["start_hour"])}


def run(model: str, region: str) -> dict:
    ctx = facts_context()
    rows, results = [json.loads(line) for line in Path("tests/agent_questions.jsonl").open()], []
    for q in rows:
        box = toolbox()
        r = answer(q["question"], box, model, region)
        text = r["text"]
        facts = [f.format(**ctx) for f in q["expected_facts"]]
        hit = all(re.search(rf"(?<!\d){re.escape(str(f))}(?!\d)", text, re.I) for f in facts)
        unmatched = verify_numbers(text, box.outputs) if r["source"] == "agent" else []
        refused = any(h in text.lower() for h in REFUSAL_HINTS)
        bad_phrase = any(b in text.lower() for b in q.get("must_not_contain", []))
        results.append({"id": q["id"], "question": q["question"], "answer": text,
                        "source": r["source"], "facts_ok": hit and not bad_phrase,
                        "unmatched": unmatched,
                        "refusal_ok": (refused if q["must_refuse"] else True)})
    n = len(results)
    return {"model": model, "n": n,
            "fact_accuracy": round(sum(r["facts_ok"] for r in results) / n, 3),
            "unmatched_numbers_shipped": sum(len(r["unmatched"]) for r in results),
            "refusals_correct": f"{sum(r['refusal_ok'] for r in results if rows[r['id'] - 1]['must_refuse'])}"
                                f"/{sum(q['must_refuse'] for q in rows)}",
            "fallbacks": sum(r["source"] == "template" for r in results),
            "results": results}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="in.anthropic.claude-sonnet-5")
    ap.add_argument("--region", default="ap-south-1")
    ap.add_argument("--out")
    a = ap.parse_args()
    report = run(a.model, a.region)
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))
    for r in report["results"]:
        if not (r["facts_ok"] and r["refusal_ok"]) or r["unmatched"]:
            print(f"- #{r['id']} {r['question']!r}: {r['answer'][:160]!r}")
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False))
