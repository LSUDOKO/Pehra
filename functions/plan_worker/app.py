"""SQS consumer: start one plan execution per site and date.

Idempotent twice over: the execution name is unique per site+date (Step Functions
rejects duplicates), and BuildPlan claims a DynamoDB idempotency key.
"""

import json
import re

import boto3

from ihcommon import config
from ihcommon.log import log


def execution_name(site_id: str, day: str, mode: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", f"{mode}-{site_id}-{day}")[:80]


def handler(event, _ctx):
    sfn = boto3.client("stepfunctions", region_name=config.REGION)
    failures = []
    for rec in event.get("Records", []):
        msg = json.loads(rec["body"])
        try:
            sfn.start_execution(stateMachineArn=config.PLAN_SFN_ARN,
                                name=execution_name(msg["site_id"], msg["date"], msg["mode"]),
                                input=json.dumps(msg))
        except sfn.exceptions.ExecutionAlreadyExists:
            log("plan_already_started", date=msg["date"])
        except Exception as e:
            log("plan_start_failed", error=str(e))
            failures.append({"itemIdentifier": rec["messageId"]})
    return {"batchItemFailures": failures}
