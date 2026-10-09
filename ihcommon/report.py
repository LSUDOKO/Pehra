"""Monthly contractor compliance report (PDF) built only from locked daily records.

Counts only: no names, no device ids. Records marked sample produce a SAMPLE watermark line.
"""

from collections import Counter

from fpdf import FPDF

from ihcommon.records import verify_chain

INK = (30, 42, 47)
SHADE = (15, 92, 77)
RED = (200, 16, 46)


def summarise_month(records: list[dict]) -> dict:
    recs = sorted(records, key=lambda r: r["date"])
    status = Counter(r["plan_status"] for r in recs)
    checks = Counter()
    for r in recs:
        checks.update(r["checkins"]["counts"])
    stop_days = sum(1 for r in recs if r["plan"] and r["plan"].get("stop_from") is not None)
    return {"days": len(recs), "plans": sum(1 for r in recs if r["plan"]), "stop_days": stop_days,
            "approved": status["approved"], "overridden": status["overridden"],
            "no_response": status["no_response"],
            "overrides": [(r["date"], o["direction"], o["reason"]) for r in recs for o in r["overrides"]],
            "recheck_alerts": sum(len(r["alerts"]) for r in recs),
            "breaks_logged": checks["break_start"], "symptom_reports": checks["symptom"],
            "chain_ok": not verify_chain(recs), "sample": any(r.get("sample") for r in recs),
            "first": recs[0]["date"] if recs else "", "last": recs[-1]["date"] if recs else "",
            "last_hash": recs[-1]["hash"] if recs else ""}


def build_pdf(records: list[dict], site_name: str) -> bytes:
    s = summarise_month(records)
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_text_color(*INK)
    if s["sample"]:
        pdf.set_text_color(*RED)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "SAMPLE DATA - for demonstration only, not a real site", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Heat safety compliance report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 7, f"{site_name}  |  {s['first']} to {s['last']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    rows = [("Days covered", s["days"]), ("Days with a heat plan", s["plans"]),
            ("Days with a stop-work window", s["stop_days"]), ("Plans approved", s["approved"]),
            ("Plans overridden (with reason)", s["overridden"]), ("Plans with no response", s["no_response"]),
            ("Midday re-check alerts", s["recheck_alerts"]), ("Breaks logged by workers", s["breaks_logged"]),
            ("Symptom reports (count only)", s["symptom_reports"])]
    pdf.set_font("Helvetica", "", 12)
    for label, val in rows:
        pdf.cell(110, 8, label, border="B")
        pdf.cell(0, 8, str(val), border="B", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Overrides and reasons", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    if not s["overrides"]:
        pdf.cell(0, 7, "None.", new_x="LMARGIN", new_y="NEXT")
    for day, direction, reason in s["overrides"]:
        pdf.multi_cell(0, 6, f"{day}  {direction}: {reason}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*(SHADE if s["chain_ok"] else RED))
    pdf.cell(0, 8, "Record integrity: " + ("hash chain verified" if s["chain_ok"] else "CHAIN BROKEN"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, f"Last record hash: {s['last_hash']}\nDaily records are SHA-256 hash-chained and "
                         "stored in S3 Object Lock. Counts only; no worker names or IDs are kept. Plans use "
                         "WBGT (heat, humidity, sun, wind) against NIOSH limits; rest bands are the "
                         "project's own planning rule. Designed to reduce exposure; not a medical record.")
    return bytes(pdf.output())
