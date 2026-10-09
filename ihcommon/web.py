"""Server-side HTML for the worker page and the printable picture poster.

All dynamic values are escaped; all plan numbers come from the heatcore plan dict.
"""

import html
from datetime import datetime
from pathlib import Path

import segno

from heatcore.templates_hi import FIRST_AID_HI, clock

WEB = Path(__file__).parent / "web"
if not WEB.exists():
    WEB = Path(__file__).parents[1] / "web"


def qr_svg(url: str, scale: int = 6) -> str:
    return segno.make(url, error="m").svg_inline(scale=scale, dark="#1E2A2F", border=2)


def plan_line(plan: dict | None) -> str:
    if not plan:
        return "Aaj ka plan abhi nahi bana."
    if plan.get("stop_from") is not None:
        return f"Aaj {clock(plan['stop_from'])} se {clock(plan['stop_to'])} baje tak kaam band."
    return "Aaj har ghante plan ke hisaab se aaram."


def worker_page(site: dict, plan: dict | None, api_url: str) -> str:
    tpl = (WEB / "worker" / "index.html").read_text()
    vals = {"SITE_NAME": html.escape(site["name"]), "PLAN_LINE": html.escape(plan_line(plan)),
            "FIRST_AID": html.escape(FIRST_AID_HI), "SITE_TOKEN": html.escape(site["site_token"]),
            "API_URL": html.escape(api_url)}
    for k, v in vals.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


STOP_ICON = ('<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M20 30V14a4 4 0 0 1 8 0v14V10'
             'a4 4 0 0 1 8 0v18V14a4 4 0 0 1 8 0v22c0 12-8 20-18 20-8 0-12-5-16-12l-6-11'
             'a4 4 0 0 1 7-4z" fill="#fff"/></svg>')
CAN_ICON = ('<svg viewBox="0 0 30 40" aria-hidden="true"><rect x="3" y="8" width="24" height="30" rx="5" '
            'fill="#2b7bb9" stroke="#1E2A2F" stroke-width="2"/><rect x="10" y="2" width="10" height="7" '
            'rx="2" fill="#1E2A2F"/></svg>')
MAX_CAN_ICONS = 12  # above this, one icon and the count, so icons never miscount


def poster_page(site: dict, plan: dict, worker_url: str) -> str:
    """Printable picture poster: a 'day ruler' readable without reading Hindi."""
    hours = plan["plans"]["moderate"]["hours"]
    cols = []
    for h in hours:
        rest = h["rest_minutes"]
        if h["status"] == "stop":
            bar = f'<div class="bar stop" title="{h["hour"]}:00 kaam band">{STOP_ICON}</div>'
        else:
            bar = (f'<div class="bar" title="{h["hour"]}:00 {rest} min aaram">'
                   f'<div class="rest" style="height:{round(rest / 60 * 100)}%"></div></div>')
        cols.append(f'<div class="hour">{bar}<b>{clock(h["hour"])}</b></div>')
    cans = plan["water"]["cans_20l"]
    icons = CAN_ICON * cans if cans <= MAX_CAN_ICONS else CAN_ICON
    can_label = f"{cans} can paani" if cans <= MAX_CAN_ICONS else f"× {cans} can paani"
    d = datetime.fromisoformat(plan["date"])
    stop = (f"{clock(plan['stop_from'])}–{clock(plan['stop_to'])} baje kaam band"
            if plan.get("stop_from") is not None else "Plan ke hisaab se aaram")
    nw = plan.get("new_workers")
    new_line = (f"<p>Naye mazdoor: sirf {round(nw['fraction'] * 100)}% kaam (din {nw['day']})</p>"
                if nw else "")
    issued = datetime.fromisoformat(plan["forecast_issued"])
    css = (WEB / "poster" / "poster.css").read_text()
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(site['name'])} · {d:%d %b}</title><style>{css}</style></head><body>
<div class="sheet" style="--n:{len(hours)}">
<header><h1>{html.escape(stop)}</h1><p>{html.escape(site['name'])} · {d:%d %b %Y}</p></header>
<div class="ruler" role="img" aria-label="Har ghante ka kaam aur aaram">{''.join(cols)}</div>
<div class="legend">
<span><i class="sw" style="background:var(--sun)"></i>Kaam</span>
<span><i class="sw" style="background:var(--shade)"></i>Aaram (chhaon)</span>
<span><i class="sw" style="background:var(--red)"></i>Kaam band</span></div>
<div class="bottom"><div><div class="water">{icons}<span>{can_label}</span></div>{new_line}
<p class="note">Forecast: {html.escape(plan['forecast_model'])}, {issued:%d %b %H:%M} IST.
WBGT (garmi + nami + dhoop) par bana plan. Yeh first aid nahi; emergency mein 108.</p></div>
<div class="qr">{qr_svg(worker_url)}Aaram ke liye scan karein</div></div>
</div></body></html>"""
