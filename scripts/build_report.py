"""Build a compliance PDF from a local folder of records (e.g. the seeded sample month).

    uv run python scripts/build_report.py out/sample_records docs/results/sample_compliance_report.pdf
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from ihcommon.report import build_pdf  # noqa: E402

if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    recs = [json.loads(p.read_text()) for p in sorted(src.glob("*.json"))]
    dst.write_bytes(build_pdf(recs, sys.argv[3] if len(sys.argv) > 3 else "Sample site (Chennai)"))
    print(f"wrote {dst} from {len(recs)} records")
