"""23:30 IST: lock each site's day into the Object Lock bucket, chained to yesterday's hash."""

import boto3

from ihcommon import config, planning, repo
from ihcommon.log import log, metric, short_hash
from ihcommon.records import GENESIS, build_record, canonical


def write_record(t, s3, site: dict, day: str) -> dict:
    sid = site["site_id"]
    head = t.get_item(Key={"PK": f"SITE#{sid}", "SK": "RECORD#head"}).get("Item") or {}
    if head.get("date") == day:
        return {"site": short_hash(sid), "result": "already_written"}
    rec = build_record(sid, day, repo.get_plan(t, sid, day), repo.day_items(t, sid, "OVR", day),
                       repo.day_items(t, sid, "ALERT", day), repo.day_items(t, sid, "CHK", day),
                       head.get("hash", GENESIS))
    key = f"records/{sid}/{day}.json"
    # Object Lock retention comes from the bucket default; a checksum is required for locked puts.
    s3.put_object(Bucket=config.RECORDS_BUCKET, Key=key, Body=canonical(rec),
                  ContentType="application/json", ChecksumAlgorithm="SHA256")
    t.put_item(Item={"PK": f"SITE#{sid}", "SK": "RECORD#head", "date": day, "hash": rec["hash"],
                     "s3_key": key})
    metric("RecordLocked")
    return {"site": short_hash(sid), "result": "locked", "hash": rec["hash"][:12]}


def handler(event, _ctx):
    t = repo.table()
    s3 = boto3.client("s3", region_name=config.REGION)
    day = (event or {}).get("date") or planning.today_ist()
    out = []
    for site in repo.list_sites(t):
        try:
            out.append(write_record(t, s3, site, day))
        except Exception as e:
            log("record_failed", site=short_hash(site["site_id"]), error=str(e)[:200])
            metric("RecordFailed")
    log("records_done", date=day, results=out)
    return {"date": day, "results": out}
