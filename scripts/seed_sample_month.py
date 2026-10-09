"""Seed a SAMPLE month of daily records (clearly labelled) for the compliance report demo.

    uv run python scripts/seed_sample_month.py --out out/sample_records

Plans come from the real engine on a synthetic hot-humid profile; approvals, overrides,
alerts and check-ins are invented and every record carries "sample": true.
"""

import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.plan import HourHeat
from ihcommon.records import GENESIS, build_record, canonical

PROFILE = [27, 27, 27, 27, 27, 27, 27, 28, 29, 30, 31, 32, 32.5, 32.5, 31.5, 30.5, 29.5, 28.5,
           28, 27.5, 27, 27, 27, 27]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/sample_records")
    ap.add_argument("--month", default="2026-05")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    first = date.fromisoformat(a.month + "-01")
    prev = GENESIS
    d = first
    while d.month == first.month:
        jitter = rnd.uniform(-2.5, 1.5)
        heat = [HourHeat(datetime(d.year, d.month, d.day, h), round(v + jitter, 1), round(v + jitter - 3, 1))
                for h, v in enumerate(PROFILE)]
        plan = build_daily_plan(heat, Crew(40, 10, rnd.choice([0, 0, 3])),
                                ForecastMeta("SAMPLE forecast", datetime.combine(d - timedelta(days=1),
                                             datetime.min.time()) + timedelta(hours=12)),
                                datetime.combine(d - timedelta(days=1), datetime.min.time()) + timedelta(hours=19),
                                site_id="sample-site", site_name="Sample site (Chennai)")
        ts = f"{d.isoformat()}T07:1{rnd.randint(0, 9)}:00+05:30"
        status = rnd.choices(["approved", "overridden", "no_response"], [0.8, 0.1, 0.1])[0]
        overrides = ([{"direction": "stricter", "reason": "Concrete pour moved to morning", "actor_role":
                       "Supervisor", "decision": "allow", "SK": f"OVR#{d}#{ts}"}] if status == "overridden" else [])
        checkins = [{"type": rnd.choice(["break_start", "break_end"]),
                     "SK": f"CHK#{d}#{d.isoformat()}T{rnd.randint(10, 16):02d}:00:00+05:30#x"}
                    for _ in range(rnd.randint(10, 40))]
        if rnd.random() < 0.15:
            checkins.append({"type": "symptom", "SK": f"CHK#{d}#{d.isoformat()}T13:20:00+05:30#y"})
        rec = build_record("sample-site", d.isoformat(), {"plan": plan, "status": status,
                                                          "approved_at": ts if status == "approved" else None},
                           overrides, [], checkins, prev, sample=True)
        (out / f"{d.isoformat()}.json").write_bytes(canonical(rec))
        prev = rec["hash"]
        d += timedelta(days=1)
    print(f"wrote sample records to {out}")


if __name__ == "__main__":
    main()
