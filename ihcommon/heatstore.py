"""Heat store on S3: one JSON object per city per forecast run (compute once, look up many).

heat/{city}/{run_id}.json  and  heat/{city}/latest.json
Sites never call a weather API; they read the latest object for their city.
"""

import json

import boto3

from heatcore.heat import heat_from_json
from heatcore.plan import HourHeat
from ihcommon import config


def _s3():
    return boto3.client("s3", region_name=config.REGION)


def put_heat(city: str, run_id: str, doc: dict, bucket: str | None = None) -> str:
    b = bucket or config.HEAT_BUCKET
    body = json.dumps(doc).encode()
    key = f"heat/{city}/{run_id}.json"
    s3 = _s3()
    s3.put_object(Bucket=b, Key=key, Body=body, ContentType="application/json")
    s3.put_object(Bucket=b, Key=f"heat/{city}/latest.json", Body=body,
                  ContentType="application/json")
    return key


def get_latest(city: str, bucket: str | None = None) -> dict:
    obj = _s3().get_object(Bucket=bucket or config.HEAT_BUCKET, Key=f"heat/{city}/latest.json")
    return json.loads(obj["Body"].read())


def hours(doc: dict) -> list[HourHeat]:
    return heat_from_json(doc["hours"])
