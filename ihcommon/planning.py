"""One place that turns (site, date) into a daily plan from the cached heat store."""

from datetime import date, datetime, timedelta

from heatcore.daily import Crew, ForecastMeta, build_daily_plan
from heatcore.heat import IST, for_date
from ihcommon import heatstore, repo


def now_ist() -> datetime:
    return datetime.now(IST).replace(tzinfo=None, microsecond=0)


def tomorrow_ist() -> str:
    return (now_ist().date() + timedelta(days=1)).isoformat()


def today_ist() -> str:
    return now_ist().date().isoformat()


def crew_for(t, site_id: str) -> Crew:
    c = repo.get_crew(t, site_id) or {}
    return Crew(headcount=c.get("headcount", 0), heavy_count=c.get("heavy_count", 0),
                new_count=c.get("new_count", 0), new_day=c.get("new_day", 1))


def forecast_meta(doc: dict) -> ForecastMeta:
    issued = datetime.fromisoformat(doc["issued_at"]).astimezone(IST).replace(tzinfo=None)
    return ForecastMeta(doc["model"], issued)


def plan_for_site(t, site: dict, day: str, *, heat_doc: dict | None = None,
                  now: datetime | None = None) -> dict:
    doc = heat_doc or heatstore.get_latest(site["city"])
    heat = for_date(heatstore.hours(doc), day)
    if not heat:
        raise ValueError(f"no forecast hours for {day} in run {doc['run_id']}")
    plan = build_daily_plan(heat, crew_for(t, site["site_id"]), forecast_meta(doc), now or now_ist(),
                            site_id=site["site_id"], site_name=site["name"],
                            site_type=site.get("site_type", "site"))
    return add_conditions(plan, doc, site["city"])


def add_conditions(plan: dict, doc: dict, key: str) -> dict:
    """Attach rain, warm-night and river-flood context (from code) and the matching site lines."""
    from heatcore.daily import plan_hash
    from heatcore.templates_people import site_night_line, site_rain_line
    from ihcommon import locdata

    try:
        normals = locdata._get_json(f"normals/{key}.json")
    except Exception:
        normals = None
    cond = locdata.conditions(doc, normals, plan["date"])
    plan["conditions"] = cond
    flood = cond.get("flood")
    lines = [site_rain_line(cond.get("rain")), site_night_line(cond.get("night")),
             "- Nadi ka paani badh sakta hai: kinare ke paas ka kaam band, raasta pehle se tay karein."
             if flood and flood.get("alert") else None]
    plan["extra_lines"] = [x for x in lines if x]
    plan["plan_hash"] = plan_hash(plan)
    return plan


def heat_days(doc: dict, start: date, days: int):
    wanted = {(start + timedelta(days=i)).isoformat() for i in range(days)}
    return [h for h in heatstore.hours(doc) if h.time_local.date().isoformat() in wanted]
