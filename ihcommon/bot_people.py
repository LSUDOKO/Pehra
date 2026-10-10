"""Personal / family mode and the water finder, shared by Telegram and WhatsApp.

Returns True when a message or button was handled here, so ihcommon.bot can fall through.
"""

from heatcore.openmeteo import geocode
from ihcommon import crypto, repo, texts
from ihcommon.log import metric
from ihcommon.people import area_for, find_water
from ihcommon.voicecall import normalise_phone

START_BUTTONS = [[("Site / school / dukaan", "mode:site"), ("Mere aur parivar ke liye", "mode:me")]]
SITE_TYPE_BUTTONS = [[("Construction site", "type:site"), ("School", "type:school"), ("Dukaan/market", "type:vendor")],
                     [("Delivery rider", "type:rider")]]
# (field, question, options as (label, value)); WhatsApp allows at most 3 buttons
HH_STEPS = [
    ("elderly", "Ghar mein 65 saal se zyada umar ke kitne log hain?", [("0", 0), ("1", 1), ("2+", 2)]),
    ("young_children", "5 saal se chhote kitne bachche hain?", [("0", 0), ("1", 1), ("2+", 2)]),
    ("pregnant", "Kya ghar mein koi garbhvati hai?", [("Nahi", 0), ("Haan", 1)]),
    ("chronic", "Dil, sugar, BP ya kidney ki bimari wale kitne log?", [("0", 0), ("1", 1), ("2+", 2)]),
    ("works_outdoors", "Kya koi dhoop mein bahar kaam karta hai?", [("Nahi", 0), ("Haan", 1)]),
]


def ask_step(d, chat_id: str, i: int) -> None:
    field, q, opts = HH_STEPS[i]
    d.bot.send_text(chat_id, q, [[(label, f"hh:{i}:{v}") for label, v in opts]])


def create_person(d, chat_id: str, owner: str, place: str, lat: float, lon: float) -> None:
    repo.put_person(d.t, owner, {"place": place[:60], "lat": round(lat, 4), "lon": round(lon, 4),
                                 "chat_enc": crypto.encrypt(chat_id, d.key), "household": {"adults": 1}})
    repo.set_chat_state(d.t, owner, None)
    metric("PersonRegistered")
    d.bot.send_text(chat_id, texts.PERSON_SAVED.format(place=place))
    ask_step(d, chat_id, 0)


def handle_location(d, chat_id: str, owner: str, lat: float, lon: float, assist) -> None:
    state = repo.get_chat_state(d.t, owner).get("awaiting")
    if state == "place":
        create_person(d, chat_id, owner, "aapki location", lat, lon)
    elif state == "add_paani":
        n = repo.report_point(d.t, area_for(lat, lon), round(lat, 4), round(lon, 4), "community_water", owner)
        repo.set_chat_state(d.t, owner, None)
        metric("WaterPointReported")
        d.bot.send_text(chat_id, texts.POINT_ADDED.format(n=n))
    else:
        metric("WaterFinderUsed")
        d.bot.send_text(chat_id, find_water(d.t, lat, lon))


def handle_message(d, chat_id: str, owner: str, text: str, cmd: str, arg: str, assist) -> bool:
    person = repo.get_person(d.t, owner)
    state = repo.get_chat_state(d.t, owner).get("awaiting")
    if cmd == "/me":
        repo.set_chat_state(d.t, owner, {"awaiting": "place"})
        d.bot.send_text(chat_id, texts.ASK_PLACE)
        return True
    if cmd == "/paani":
        repo.set_chat_state(d.t, owner, {"awaiting": "paani"})
        d.bot.send_text(chat_id, texts.ASK_LOCATION_PAANI)
        return True
    if cmd == "/add_paani":
        repo.set_chat_state(d.t, owner, {"awaiting": "add_paani"})
        d.bot.send_text(chat_id, texts.ASK_LOCATION_ADD)
        return True
    if state == "place" and text and not text.startswith("/"):
        hit = geocode(text)
        if not hit:
            d.bot.send_text(chat_id, texts.PLACE_NOT_FOUND)
        else:
            create_person(d, chat_id, owner, hit["name"], hit["lat"], hit["lon"])
        return True
    if cmd in ("/aaj", "/ghar", "/family_call", "/family_call_off"):
        if not person:
            d.bot.send_text(chat_id, texts.NOT_PERSON)
            return True
        if cmd == "/aaj":
            assist({"kind": "personal_today", "owner": owner})
            d.bot.send_text(chat_id, texts.WORKING)
        elif cmd == "/ghar":
            ask_step(d, chat_id, 0)
        elif cmd == "/family_call":
            phone = normalise_phone(arg) if arg.strip() else None
            if not phone:
                d.bot.send_text(chat_id, texts.FAMILY_ASK)
            else:
                repo.update_person(d.t, owner, family_enc=crypto.encrypt(phone, d.key))
                metric("FamilyCallOptIn")
                d.bot.send_text(chat_id, texts.FAMILY_ON.format(last4=phone[-4:]))
        else:
            repo.update_person(d.t, owner, family_enc=None)
            d.bot.send_text(chat_id, texts.FAMILY_OFF)
        return True
    return False


def handle_callback(d, chat_id: str, owner: str, kind: str, arg: str, assist) -> bool:
    if kind == "mode":
        if arg == "me":
            repo.set_chat_state(d.t, owner, {"awaiting": "place"})
            d.bot.send_text(chat_id, texts.ASK_PLACE)
        else:
            d.bot.send_text(chat_id, "Site jodne ke liye: /register Site ka naam, shahar")
        return True
    if kind == "hh":
        person = repo.get_person(d.t, owner)
        if not person:
            d.bot.send_text(chat_id, texts.NOT_PERSON)
            return True
        i, v = (int(x) for x in arg.split(":"))
        field = HH_STEPS[i][0]
        hh = dict(person.get("household") or {})
        hh[field] = bool(v) if field == "works_outdoors" else v
        repo.update_person(d.t, owner, household=hh)
        if i + 1 < len(HH_STEPS):
            ask_step(d, chat_id, i + 1)
        else:
            d.bot.send_text(chat_id, texts.PROFILE_DONE)
            assist({"kind": "personal_today", "owner": owner})
        return True
    return False
