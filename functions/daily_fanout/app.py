"""19:00 IST: put one message per registered site on the plan queue (fan-out)."""

import json

import boto3

from ihcommon import config, planning, repo
from ihcommon.log import log, metric


def handler(event, _ctx):
    day = (event or {}).get("date") or planning.tomorrow_ist()
    sqs = boto3.client("sqs", region_name=config.REGION)
    sites = repo.list_sites(repo.table())
    for i in range(0, len(sites), 10):
        batch = sites[i:i + 10]
        sqs.send_message_batch(QueueUrl=config.PLAN_QUEUE_URL, Entries=[
            {"Id": str(n), "MessageBody": json.dumps({"site_id": s["site_id"], "date": day,
                                                     "mode": "scheduled"})}
            for n, s in enumerate(batch)])
    metric("PlansQueued", len(sites))
    log("fanout_done", sites=len(sites), date=day)
    return {"queued": len(sites), "date": day}
