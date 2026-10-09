"""Environment config and cached SSM SecureString parameters."""

import functools
import os

import boto3

TABLE = os.environ.get("TABLE_NAME", "InvisibleHeat")
HEAT_BUCKET = os.environ.get("HEAT_BUCKET", "")
MEDIA_BUCKET = os.environ.get("MEDIA_BUCKET", "")
RECORDS_BUCKET = os.environ.get("RECORDS_BUCKET", "")
OUT_QUEUE_URL = os.environ.get("OUT_QUEUE_URL", "")
PLAN_QUEUE_URL = os.environ.get("PLAN_QUEUE_URL", "")
PLAN_SFN_ARN = os.environ.get("PLAN_SFN_ARN", "")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "")
PARAM_PREFIX = os.environ.get("PARAM_PREFIX", "/invisible-heat")
REGION = os.environ.get("AWS_REGION", "ap-south-1")
BEDROCK_MODEL_FAST = os.environ.get("BEDROCK_MODEL_FAST", "")
BEDROCK_MODEL_QA = os.environ.get("BEDROCK_MODEL_QA", "")
AGENT_ENABLED = os.environ.get("AGENT_ENABLED", "true") == "true"


@functools.cache
def param(name: str) -> str:
    """Read a SecureString from SSM once per container (e.g. 'telegram-token')."""
    ssm = boto3.client("ssm", region_name=REGION)
    return ssm.get_parameter(Name=f"{PARAM_PREFIX}/{name}", WithDecryption=True)["Parameter"]["Value"]


def learn_base_url(event: dict) -> None:
    """Use the API's own domain for public links unless PUBLIC_BASE_URL is set (avoids a stack cycle)."""
    global PUBLIC_BASE_URL
    domain = (event.get("requestContext") or {}).get("domainName")
    if not PUBLIC_BASE_URL and domain:
        PUBLIC_BASE_URL = f"https://{domain}"
