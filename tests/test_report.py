import json
import subprocess
import sys
from pathlib import Path

from ihcommon.report import build_pdf, summarise_month


def test_report_from_sample_month(tmp_path):
    root = Path(__file__).parents[1]
    subprocess.run([sys.executable, str(root / "scripts/seed_sample_month.py"), "--out", str(tmp_path)],
                   check=True, cwd=root)
    recs = [json.loads(p.read_text()) for p in sorted(tmp_path.glob("*.json"))]
    s = summarise_month(recs)
    assert s["days"] == 31 and s["chain_ok"] and s["sample"]
    pdf = build_pdf(recs, "Sample site")
    assert pdf[:4] == b"%PDF" and len(pdf) > 1000
