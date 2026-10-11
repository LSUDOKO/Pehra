"""Build the static audit and model-card pages from result JSON (numbers come from code).

    uv run python scripts/build_pages.py
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
CSS = (ROOT / "web/india.css").read_text()


def page(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)} · Pehra</title><style>{CSS}</style>"
            '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&amp;family=Manrope:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet"></head><body>'
            '<nav class="page-nav" aria-label="Main navigation"><a class="page-brand" href="/">प Pehra</a>'
            '<a href="/audit">Audit</a><a href="/model-card">Method &amp; limits</a></nav>'
            f'<main><span class="page-kicker">Pehra · Evidence and method</span>{body}</main>'
            '<footer class="page-foot">Team Mavricks · <a href="/">Back to Pehra</a></footer></body></html>')


def audit_page(s: dict) -> str:
    t = s["total"]
    top = max(d["invisible_days_shade"] for d in s["districts"]) or 1
    rows = "".join(
        f"<tr><td>{html.escape(d['city'])}</td>"
        f"<td class='n'>{d['invisible_days_shade']}</td>"
        f"<td class='vis'><div class='bar' style='width:{d['invisible_days_shade'] / top * 100:.0f}%'></div></td>"
        f"<td class='n'>{d['invisible_shade_outside_mar_jun']}</td>"
        f"<td class='n'>{d['heatwave_days']}</td>"
        f"<td class='n'>{d.get('warm_nights', '–')}</td>"
        f"<td class='n'>{d.get('heavy_rain_days', '–')}</td></tr>"
        for d in sorted(s["districts"], key=lambda d: -d["invisible_days_shade"]))
    share = round(100 * t["invisible_days_shade"] / max(t["danger_days_shade"], 1))
    caveats = "".join(f"<li>{html.escape(c)}</li>" for c in s["caveats"])
    body = f"""
<h1>Invisible heat days</h1>
<p class="lede">Days when heat and humidity together crossed the NIOSH work limit, but India's
temperature-based heatwave rule would not have raised an alarm. {html.escape(s['period'][0][:4])}–{html.escape(s['period'][1][:4])}, {len(s['districts'])} cities.</p>
<p class="big">{t['invisible_days_shade']:,}</p>
<p>city-days with WBGT in the shade above the NIOSH limit for moderate work ({t['limit_c']} °C)
and no heatwave under the recreated rule — {share}% of all such days. {t['invisible_shade_outside_mar_jun']:,} of them fell
outside March–June, when heatwave bulletins do not run.</p>
<h2>The water side</h2>
<p>The same five years held <b>{t.get('heavy_rain_days', 0):,}</b> city-days of heavy rain (IMD "heavy", 64.5 mm or more in a day) and
<b>{t.get('warm_nights', 0):,}</b> warm nights, when the body cannot cool down after a hot day. Pehra adds both to its plans.</p>
<div class="caveat"><b>These numbers are a minimum.</b><ul>{caveats}</ul></div>
<h2>By city</h2>
<div class="table-scroll" role="region" aria-label="Audit results by city" tabindex="0"><table><thead><tr><th>City</th><th style="text-align:right">Invisible heat days</th><th class="vis"></th>
<th style="text-align:right">Outside Mar–Jun</th><th style="text-align:right">Heatwave days (recreated rule)</th>
<th style="text-align:right">Warm nights</th><th style="text-align:right">Heavy-rain days</th></tr></thead>
<tbody>{rows}</tbody></table></div>
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
    return page("Pehra model card", "\n".join(out))


def home_page(s: dict) -> str:
    """Landing page: fill the template with numbers from the audit and the Kharghar replay."""
    t = s["total"]
    k = json.loads((ROOT / "docs/results/kharghar_replay.json").read_text())
    noon = next(h["wbgt_sun"] for h in k["hours"] if h["hour"] == 12)
    vals = {"N_INVISIBLE": f"{t['invisible_days_shade']:,}", "N_OUTSIDE": f"{t['invisible_shade_outside_mar_jun']:,}",
            "N_CITIES": str(len(s["districts"])), "N_RAIN": f"{t.get('heavy_rain_days', 0):,}",
            "N_NIGHTS": f"{t.get('warm_nights', 0):,}", "K_TMAX": str(k["imd"]["tmax_c"]), "K_WBGT": str(noon),
            "LIMIT": str(t["limit_c"]), "N_INVISIBLE_RAW": str(t["invisible_days_shade"]),
            "N_OUTSIDE_RAW": str(t["invisible_shade_outside_mar_jun"])}
    tpl = (ROOT / "web/home/template.html").read_text()
    for key, v in vals.items():
        tpl = tpl.replace("{{" + key + "}}", html.escape(v))
    assert "{{" not in tpl, "unfilled placeholder in home page"
    return tpl


if __name__ == "__main__":
    summary = json.loads((ROOT / "docs/results/audit_summary.json").read_text())
    if (ROOT / "web/home/template.html").exists():  # the landing page may also be edited by hand
        (ROOT / "web/home/index.html").write_text(home_page(summary))
    (ROOT / "web/audit/index.html").write_text(audit_page(summary))
    card = ROOT / "docs/MODEL_CARD.md"
    if card.exists():
        (ROOT / "web/model_card").mkdir(exist_ok=True)
        (ROOT / "web/model_card/index.html").write_text(model_card_page(card.read_text()))
    print("pages built")
