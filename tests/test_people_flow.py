import json

from ihcommon import bot_people, people, repo
from tests.test_webhook import env, msg, tap  # noqa: F401  (fixture + helpers)


def location(app, lat, lon, chat=111):
    body = {"message": {"chat": {"id": chat}, "location": {"latitude": lat, "longitude": lon}}}
    return app.handler({"headers": {"X-Telegram-Bot-Api-Secret-Token": "s3cret"}, "body": json.dumps(body)}, None)


def owner_of(d, chat="111"):
    from ihcommon import crypto
    return crypto.keyed_hash(chat, d.key)


def test_start_offers_two_modes(env):  # noqa: F811
    app, d = env
    msg(app, "/start")
    assert [b[1] for b in d.bot.sent[-1][2][0]] == ["mode:site", "mode:me"]


def test_personal_onboarding_with_city_and_household(env, monkeypatch):  # noqa: F811
    app, d = env
    monkeypatch.setattr(bot_people, "geocode", lambda name: {"name": "Varanasi", "lat": 25.3176, "lon": 83.0106})
    tap(app, "mode:me")
    msg(app, "Varanasi")
    assert "Varanasi" in d.bot.sent[-2][1] and d.bot.sent[-1][2][0][0][1] == "hh:0:0"
    for i, v in enumerate([1, 0, 0, 1, 1]):
        tap(app, f"hh:{i}:{v}")
    p = repo.get_person(d.t, owner_of(d))
    assert p["household"] == {"adults": 1, "elderly": 1, "young_children": 0, "pregnant": 0, "chronic": 1,
                              "works_outdoors": True}
    assert d.lam.calls[-1] == {"kind": "personal_today", "owner": owner_of(d)}
    assert "111" not in json.dumps(p)


def test_location_onboarding_and_family_call(env):  # noqa: F811
    app, d = env
    tap(app, "mode:me")
    location(app, 28.61, 77.21)
    assert repo.get_person(d.t, owner_of(d))["lat"] == 28.61
    msg(app, "/family_call 9876543210")
    assert "3210" in d.bot.sent[-1][1] and repo.get_person(d.t, owner_of(d))["family_enc"]
    msg(app, "/family_call_off")
    assert "family_enc" not in repo.get_person(d.t, owner_of(d))


def test_water_finder_and_community_points(env, monkeypatch):  # noqa: F811
    app, d = env
    monkeypatch.setattr(people, "_places_for", lambda area: [
        {"lat": 28.6316, "lon": 77.2168, "kind": "drinking_water", "name": "Pyau"}])
    location(app, 28.6315, 77.2167)
    assert "Pyau" in d.bot.sent[-1][1] and "maps.google.com" in d.bot.sent[-1][1]
    for chat in (111, 222):
        msg(app, "/add_paani", chat=chat)
        location(app, 28.6400, 77.2200, chat=chat)
    assert "2 logon" in d.bot.sent[-1][1]
    assert len(repo.community_points(d.t, "delhi")) == 1


def test_person_can_delete_data(env):  # noqa: F811
    app, d = env
    tap(app, "mode:me")
    location(app, 28.61, 77.21)
    msg(app, "/delete_my_data")
    tap(app, "del_yes")
    assert repo.get_person(d.t, owner_of(d)) is None
