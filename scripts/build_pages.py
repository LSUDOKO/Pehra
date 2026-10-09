"""Build the static audit and model-card pages from result JSON (numbers come from code).

    uv run python scripts/build_pages.py
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
CSS = (ROOT / "web/site.css").read_text()


def page(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>{body}"
            f"</main></body></html>")


def audit_page(s: dict) -> str:
    t = s["total"]
    top = max(d["invisible_days_shade"] for d in s["districts"]) or 1
    rows = "".join(
        f"<tr><td>{html.escape(d['city'])}</td>"
        f"<td class='n'>{d['invisible_days_shade']}</td>"
        f"<td class='vis'><div class='bar' style='width:{d['invisible_days_shade'] / top * 100:.0f}%'></div></td>"
        f"<td class='n'>{d['invisible_shade_outside_mar_jun']}</td>"
        f"<td class='n'>{d['heatwave_days']}</td></tr>"
        for d in sorted(s["districts"], key=lambda d: -d["invisible_days_shade"]))
    share = round(100 * t["invisible_days_shade"] / max(t["danger_days_shade"], 1))
    caveats = "".join(f"<li>{html.escape(c)}</li>" for c in s["caveats"])
    body = f"""
<h1>Invisible heat days</h1>
<p class="lede">Days when heat and humidity together crossed the NIOSH work limit, but India's
temperature-based heatwave rule would not have raised an alarm. {html.escape(s['period'][0][:4])}–{html.escape(s['period'][1][:4])}, ten cities.</p>
<p class="big">{t['invisible_days_shade']:,}</p>
<p>city-days with WBGT in the shade above the NIOSH limit for moderate work ({t['limit_c']} °C)
and no heatwave declared — {share}% of all such days. {t['invisible_shade_outside_mar_jun']:,} of them fell
outside March–June, when heatwave bulletins do not run.</p>
<div class="caveat"><b>These numbers are a minimum.</b><ul>{caveats}</ul></div>
<h2>By city</h2>
<table><thead><tr><th>City</th><th style="text-align:right">Invisible heat days</th><th class="vis"></th>
<th style="text-align:right">Outside Mar–Jun</th><th style="text-align:right">Heatwave days (recreated rule)</th></tr></thead>
<tbody>{rows}</tbody></table>
<h2>How it was counted</h2>
<p>{html.escape(s['definition'])} In the sun, {t['invisible_days_sun']:,} city-days crossed the same limit.</p>
<p>Source: {html.escape(s['source'])}. WBGT by the Liljegren method (thermofeel, Apache-2.0). Code:
<code>scripts/run_audit.py</code>. <a href="/model-card">Model card</a>.</p>"""
    return page("Invisible heat days", body)


def model_card_page(md: str) -> str:
    # The model card is written in Markdown; render a simple, safe subset.
    out, in_list = [], False
    for line in md.splitlines():
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(line[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip():
            out.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        out.append("</ul>")
    return page("Invisible Heat model card", "\n".join(out))


if __name__ == "__main__":
    summary = json.loads((ROOT / "docs/results/audit_summary.json").read_text())
    (ROOT / "web/audit/index.html").write_text(audit_page(summary))
    card = ROOT / "docs/MODEL_CARD.md"
    if card.exists():
        (ROOT / "web/model_card").mkdir(exist_ok=True)
        (ROOT / "web/model_card/index.html").write_text(model_card_page(card.read_text()))
    print("pages built")
