"""Personal and family service: today's forecast message, family call and the water/shade finder."""

import json
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError

from heatcore.cities import nearest_city
from heatcore.heat import IST, for_date, heat_from_json
from heatcore.margin import planning_margin
from heatcore.personal import AVOID_FROM_LEVEL, LEVELS, Household, personal_forecast
from heatcore.places import map_link, nearest
from heatcore.templates_hi import forecast_line
from heatcore.templates_people import family_call_text, personal_message, places_reply
from ihcommon import config, locdata, repo

CALL_FROM_LEVEL = AVOID_FROM_LEVEL  # family call only on 'bahut_zyada' or 'khatarnak' days


def household(person: dict) -> Household:
    h = person.get("household") or {}
    return Household(adults=h.get("adults", 1), elderly=h.get("elderly", 0),
                     young_children=h.get("young_children", 0), pregnant=h.get("pregnant", 0),
                     chronic=h.get("chronic", 0), works_outdoors=bool(h.get("works_outdoors", False)))


def today(person: dict, now_utc: datetime | None = None) -> dict:
    """{'text', 'forecast', 'conditions', 'call_text' (or None)} for the person's location today."""
    now_utc = now_utc or datetime.now(UTC)
    now_local = now_utc.astimezone(IST).replace(tzinfo=None)
    day = now_local.date().isoformat()
    doc = locdata.get_doc(person["lat"], person["lon"], now_utc)
    key, klat, klon, river = locdata.location_key(person["lat"], person["lon"])
    heat = for_date(heat_from_json(doc["hours"]), day)
    issued = datetime.fromisoformat(doc["issued_at"]).astimezone(IST).replace(tzinfo=None)
    margin, stale = planning_margin(issued, now_local)
    f = personal_forecast(heat, household(person), margin_c=margin)
    try:
        normals = locdata.get_normals(key, klat, klon, river)
    except Exception:
        normals = None
    cond = locdata.conditions(doc, normals, day)
    meta = {"forecast_issued": issued.isoformat(), "forecast_model": doc["model"], "stale": stale}
    fl = forecast_line(meta)
    text = personal_message(person.get("place", ""), f, cond, fl)
    call = (family_call_text(person.get("place", ""), f)
            if LEVELS.index(f["overall_level"]) >= CALL_FROM_LEVEL else None)
    return {"text": text, "forecast": f, "conditions": cond, "call_text": call}


def ask(person: dict, question: str, model_id: str, region: str, now_utc: datetime | None = None) -> str:
    """Answer a family's free-text question with the agent; fall back to today's fixed message."""
    from agent.agent import answer_personal
    from agent.people_tools import PersonalToolBox

    now_utc = now_utc or datetime.now(UTC)
    now_local = now_utc.astimezone(IST).replace(tzinfo=None)
    doc = locdata.get_doc(person["lat"], person["lon"], now_utc)
    key, klat, klon, river = locdata.location_key(person["lat"], person["lon"])
    issued = datetime.fromisoformat(doc["issued_at"]).astimezone(IST).replace(tzinfo=None)
    margin, _ = planning_margin(issued, now_local)
    try:
        normals = locdata.get_normals(key, klat, klon, river)
    except Exception:
        normals = None
    box = PersonalToolBox(person.get("place", ""), household(person), doc, margin,
                          locdata.conditions(doc, normals, now_local.date().isoformat()), now_local)
    r = answer_personal(question, box, model_id, region)
    if r["text"]:
        return r["text"]
    return "Abhi AI jawab nahi de pa raha. Aaj ka tay plan:\n\n" + today(person, now_utc)["text"]


# ---- water and shade finder -----------------------------------------------------------

def _places_for(area: str) -> list[dict]:
    try:
        obj = boto3.client("s3", region_name=config.REGION).get_object(
            Bucket=config.HEAT_BUCKET, Key=f"places/{area}.json")
        return json.loads(obj["Body"].read())["points"]
    except ClientError:
        return []


def area_for(lat: float, lon: float) -> str:
    c = nearest_city(lat, lon, 60.0)
    return c.key if c else locdata.location_key(lat, lon)[0]


def find_water(t, lat: float, lon: float) -> str:
    area = area_for(lat, lon)
    pts = _places_for(area) + repo.community_points(t, area)
    near = nearest(pts, lat, lon, k=3, max_km=5.0)
    for p in near:
        p["link"] = map_link(p["lat"], p["lon"])
    return places_reply(near, len(pts))
