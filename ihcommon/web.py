"""Server-side HTML for the worker page and the printable picture poster.

All dynamic values are escaped; all plan numbers come from the heatcore plan dict.
"""

import html
import io
from datetime import datetime
from pathlib import Path

import segno

from heatcore.templates_hi import FIRST_AID_HI, clock

WEB = Path(__file__).parent / "web"
if not WEB.exists():
    WEB = Path(__file__).parents[1] / "web"


def qr_svg(url: str, scale: int = 6) -> str:
    buf = io.StringIO()
    segno.make(url, error="m").save(buf, kind="svg", scale=scale, xmldecl=False, svgns=True,
                                    dark="#1E2A2F", border=2)
    return buf.getvalue()


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
