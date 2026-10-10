"""Channel-agnostic supervisor bot logic (Telegram and WhatsApp share it).

`d` carries: t (DynamoDB table), bot (a Channel), key (data key), sfn, lam.
Chat ids are channel-qualified: Telegram ids as-is, WhatsApp ids as "wa:<number>".
"""

import json
import os
import re
import time

from agent.roster import parse_crew_roster, readback
from heatcore.cities import get_city
from heatcore.daily import SITE_TYPES
from heatcore.templates_hi import CALL_TEST_HI
from ihcommon import authz, bot_people, config, crypto, outbox, planning, repo, texts
from ihcommon.channels import is_whatsapp
from ihcommon.log import log, metric
from ihcommon.voicecall import normalise_phone

ASSISTANT_FN = os.environ.get("ASSISTANT_FN", "")


# ---- commands -----------------------------------------------------------------

def cmd_register(d, chat_id: str, owner: str, arg: str) -> str:
    if repo.site_for_chat(d.t, owner):
        return "Aapki site pehle se judi hai. /links dekhiye."
    m = re.match(r"\s*(.+?)\s*,\s*(.+?)\s*$", arg or "")
    if not m:
        return "Aise likhiye: /register Site ka naam, shahar"
    try:
        city = get_city(m.group(2))
    except KeyError as e:
        return str(e).strip("'\"")
    site = {"site_id": f"site-{crypto.new_site_token()[:8].lower()}", "name": m.group(1)[:60],
            "city": city.key, "lat": city.lat, "lon": city.lon,
            "site_token": crypto.new_site_token(), "tenant_id": "default"}
    repo.put_site(d.t, site, owner, crypto.encrypt(chat_id, d.key))
    metric("SiteRegistered")
    return f"Site judi: {site['name']} ({city.name}).\n\n" + links_text(site) + "\n\n" + texts.HELP


def links_text(site: dict) -> str:
    base = config.PUBLIC_BASE_URL.rstrip("/")
    return (f"Mazdoor QR page: {base}/s/{site['site_token']}\n"
            f"Aaj ka poster (print karke lagaiye): {base}/p/{site['site_token']}")


def cmd_crew(d, owner: str, arg: str) -> tuple[str, list | None]:
    nums = [int(n) for n in re.findall(r"\d+", arg or "")]
    if nums:
        r = {"headcount": nums[0], "heavy_count": nums[1] if len(nums) > 1 else 0,
             "new_count": nums[2] if len(nums) > 2 else 0, "confidence": 1.0}
        if len(nums) > 3:
            r["new_day"] = nums[3]
    else:
        r = parse_crew_roster(arg or "")
    return propose_crew(d, owner, r)


def propose_crew(d, owner: str, r: dict) -> tuple[str, list | None]:
    if r.get("confidence", 0) < 1.0 or r["headcount"] is None:
        return texts.CREW_UNSURE, None
    if r["heavy_count"] + r["new_count"] > r["headcount"]:
        return texts.CREW_UNSURE, None
    pending = {k: r[k] for k in ("headcount", "heavy_count", "new_count")}
    pending["new_day"] = r.get("new_day", 1)
    repo.set_chat_state(d.t, owner, {"pending_crew": pending})
    return readback(r), [[("Haan, sahi", "crew_ok"), ("Nahi", "crew_no")]]


def cmd_plan_now(d, site: dict, arg: str) -> str:
    day = planning.today_ist() if (arg or "").strip().lower() in ("aaj", "today") else planning.tomorrow_ist()
    name = f"ondemand-{site['site_id']}-{day}-{int(time.time())}"
    d.sfn.start_execution(stateMachineArn=config.PLAN_SFN_ARN, name=name,
                          input=json.dumps({"site_id": site["site_id"], "date": day, "mode": "on_demand"}))
    return f"Plan ban raha hai ({day}). Thodi der mein aayega."


# ---- approve / override ---------------------------------------------------------

def resume(d, site_id: str, day: str, output: dict) -> bool:
    plan = repo.get_plan(d.t, site_id, day)
    token = (plan or {}).get("task_token")
    if not token:
        return False
    try:
        d.sfn.send_task_success(taskToken=token, output=json.dumps(output))
    except Exception as e:  # already resumed or timed out; the DynamoDB status is still updated
        log("resume_failed", error=type(e).__name__)
    return True


def approve(d, site: dict, day: str) -> str:
    plan = repo.get_plan(d.t, site["site_id"], day)
    if not plan:
        return texts.NO_PLAN
    principal = authz.uid("Supervisor", site["owner_hash"])
    ents = authz.site_entities(site) + [authz.plan_entity(site, day)]
    if not authz.authorize(principal, "ApprovePlan", authz.uid("Plan", f"{site['site_id']}#{day}"), ents):
        return texts.OVERRIDE_DENIED
    repo.update_plan(d.t, site["site_id"], day, status="approved", approved_at=planning.now_ist().isoformat())
    resume(d, site["site_id"], day, {"decision": "approve"})
    metric("PlanApproved")
    return texts.APPROVED


def apply_override(d, site: dict, owner: str, state: dict, reason: str) -> str:
    day, direction = state["date"], state["direction"]
    action = "LoosenPlan" if direction == "looser" else "StrictenPlan"
    ents = authz.site_entities(site) + [authz.plan_entity(site, day)]
    allowed = authz.authorize(authz.uid("Supervisor", owner), action,
                              authz.uid("Plan", f"{site['site_id']}#{day}"), ents,
                              {"reason_length": len(reason.strip()), "direction": direction})
    repo.put_override(d.t, site["site_id"], day, direction, reason.strip()[:500], "Supervisor",
                      "allow" if allowed else "deny")
    if not allowed:
        metric("OverrideDenied", direction=direction)
        return texts.REASON_TOO_SHORT if len(reason.strip()) < 10 else texts.OVERRIDE_DENIED
    repo.set_chat_state(d.t, owner, None)
    repo.update_plan(d.t, site["site_id"], day, status="overridden", override_direction=direction)
    resume(d, site["site_id"], day, {"decision": "override", "direction": direction})
    metric("PlanOverridden", direction=direction)
    return texts.OVERRIDDEN


# ---- dispatch -----------------------------------------------------------------------

START_LINKS = {"me": "/me", "paani": "/paani", "family": "/family_call", "site": "/help"}
ALIASES = {"start": "/start", "hi": "/start", "hello": "/start", "namaste": "/start", "help": "/help",
           "plan": "/plan_now", "links": "/links", "crew": "/crew", "call": "/test_call"}


def cmd_call_on(d, chat_id: str, site: dict, arg: str) -> str:
    """Opt in to Hindi voice-call alerts. WhatsApp chats can use their own number."""
    raw = arg.strip() or (chat_id if is_whatsapp(chat_id) else "")
    phone = normalise_phone(raw) if raw else None
    if not phone:
        return texts.CALL_ASK_NUMBER
    repo.set_site_fields(d.t, site["site_id"], call_enc=crypto.encrypt(phone, d.key))
    metric("CallOptIn")
    return texts.CALL_ON.format(last4=phone[-4:])


def on_callback(d, cb: dict) -> None:
    chat_id = str(cb["message"]["chat"]["id"])
    owner = crypto.keyed_hash(chat_id, d.key)
    data, reply, buttons = cb.get("data", ""), None, None
    d.bot.answer_button(cb["id"])
    kind, _, arg = data.partition(":")
    if bot_people.handle_callback(d, chat_id, owner, kind, arg, lambda p: async_assist(d, p)):
        return
    site = repo.site_for_chat(d.t, owner)
    if kind == "del_yes":
        if site:
            repo.delete_site_data(d.t, site)
        repo.delete_person(d.t, owner)
        d.bot.send_text(chat_id, texts.DELETED)
        return
    if not site:
        d.bot.send_text(chat_id, texts.NOT_REGISTERED)
        return
    if kind == "type" and arg in SITE_TYPES:
        repo.set_site_fields(d.t, site["site_id"], site_type=arg)
        reply = texts.SITE_TYPE_SAVED
    elif kind == "ap":
        reply = approve(d, site, arg)
    elif kind == "ov":
        reply = "Plan ko kaise badalna hai?"
        buttons = [[("Zyada sakht", f"ovs:{arg}"), ("Dheela", f"ovl:{arg}")]]
    elif kind in ("ovs", "ovl"):
        direction = "stricter" if kind == "ovs" else "looser"
        repo.set_chat_state(d.t, owner, {"awaiting": "reason", "date": arg, "direction": direction})
        reply = texts.ASK_REASON_STRICTER if direction == "stricter" else texts.ASK_REASON_LOOSER
    elif kind == "ack":
        repo.ack_alert(d.t, site["site_id"], arg)
        reply = texts.ACKED
    elif kind in ("crew_ok", "crew_no"):
        state = repo.get_chat_state(d.t, owner)
        if kind == "crew_ok" and state.get("pending_crew"):
            repo.put_crew(d.t, site["site_id"], planning.today_ist(), state["pending_crew"])
            reply = texts.CREW_SAVED
        else:
            reply = texts.CREW_UNSURE
        repo.set_chat_state(d.t, owner, None)
    if reply:
        d.bot.send_text(chat_id, reply, buttons)


def on_message(d, msg: dict) -> None:
    chat_id = str(msg["chat"]["id"])
    owner = crypto.keyed_hash(chat_id, d.key)
    text = (msg.get("text") or "").strip()
    cmd, _, arg = text.partition(" ")
    cmd = ALIASES.get(cmd.split("@")[0].lower(), cmd.split("@")[0].lower())
    assist = lambda p: async_assist(d, p)  # noqa: E731
    if msg.get("location"):
        loc = msg["location"]
        bot_people.handle_location(d, chat_id, owner, float(loc["latitude"]), float(loc["longitude"]), assist)
        return
    if cmd == "/start" and arg.strip() in START_LINKS:  # deep links from the website
        cmd, arg = START_LINKS[arg.strip()], ""
    if cmd == "/start":
        d.bot.send_text(chat_id, texts.PRIVACY)
        d.bot.send_text(chat_id, texts.START_CHOICE, bot_people.START_BUTTONS)
        return
    if cmd == "/register":
        reply = cmd_register(d, chat_id, owner, arg)
        d.bot.send_text(chat_id, reply)
        if reply.startswith("Site judi"):
            d.bot.send_text(chat_id, texts.SITE_TYPE_ASK, bot_people.SITE_TYPE_BUTTONS)
        return
    if bot_people.handle_message(d, chat_id, owner, text, cmd, arg, assist):
        return
    site = repo.site_for_chat(d.t, owner)
    if not site:
        person = repo.get_person(d.t, owner)
        if person and cmd == "/delete_my_data":
            d.bot.send_text(chat_id, "Pakka sab data mitana hai?", [[("Haan, mitao", "del_yes")]])
        else:
            d.bot.send_text(chat_id, texts.PEOPLE_HELP if person else texts.NOT_REGISTERED)
        return
    reply, buttons = None, None
    if msg.get("voice"):
        async_assist(d, {"kind": "voice", "site_id": site["site_id"], "chat_enc": site["chat_enc"],
                         "owner": owner, "file_id": msg["voice"]["file_id"]})
        reply = texts.WORKING
    elif cmd == "/help":
        reply = texts.HELP
    elif cmd == "/links":
        reply = links_text(site)
    elif cmd == "/crew":
        reply, buttons = cmd_crew(d, owner, arg)
    elif cmd == "/plan_now":
        reply = cmd_plan_now(d, site, arg)
    elif cmd == "/call_on":
        reply = cmd_call_on(d, chat_id, site, arg)
    elif cmd == "/call_off":
        repo.set_site_fields(d.t, site["site_id"], call_enc=None)
        reply = texts.CALL_OFF
    elif cmd == "/test_call":
        reply = texts.CALL_TEST_QUEUED if outbox.enqueue_call(site, CALL_TEST_HI) else texts.CALL_NOT_ON
    elif cmd == "/delete_my_data":
        reply, buttons = "Pakka sab data mitana hai?", [[("Haan, mitao", "del_yes")]]
    elif text:
        state = repo.get_chat_state(d.t, owner)
        roster = parse_crew_roster(text)
        if state.get("awaiting") == "reason":
            reply = apply_override(d, site, owner, state, text)
        elif roster["confidence"] == 1.0 and not text.endswith("?"):
            reply, buttons = propose_crew(d, owner, roster)
        else:
            async_assist(d, {"kind": "question", "site_id": site["site_id"],
                             "chat_enc": site["chat_enc"], "text": text[:1000]})
            reply = texts.WORKING
    if reply:
        d.bot.send_text(chat_id, reply, buttons)


def async_assist(d, payload: dict) -> None:
    d.lam.invoke(FunctionName=ASSISTANT_FN, InvocationType="Event", Payload=json.dumps(payload).encode())
