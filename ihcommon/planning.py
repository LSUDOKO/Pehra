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
    return build_daily_plan(heat, crew_for(t, site["site_id"]), forecast_meta(doc),
                            now or now_ist(), site_id=site["site_id"], site_name=site["name"])


def heat_days(doc: dict, start: date, days: int):
    wanted = {(start + timedelta(days=i)).isoformat() for i in range(days)}
    return [h for h in heatstore.hours(doc) if h.time_local.date().isoformat() in wanted]
