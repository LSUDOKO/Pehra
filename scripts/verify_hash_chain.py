"""Verify a site's daily record chain, from S3 or a local folder of JSON records.

    uv run python scripts/verify_hash_chain.py --bucket BUCKET --site SITE_ID
    uv run python scripts/verify_hash_chain.py --dir path/to/records
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from ihcommon.records import verify_chain  # noqa: E402


def load_s3(bucket: str, site: str, region: str) -> list[dict]:
    import boto3
    s3 = boto3.client("s3", region_name=region)
    keys = [o["Key"] for page in s3.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=f"records/{site}/") for o in page.get("Contents", [])]
    return [json.loads(s3.get_object(Bucket=bucket, Key=k)["Body"].read()) for k in keys]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket")
    ap.add_argument("--site")
    ap.add_argument("--dir")
    ap.add_argument("--region", default="ap-south-1")
    a = ap.parse_args()
    recs = ([json.loads(p.read_text()) for p in sorted(Path(a.dir).glob("*.json"))] if a.dir
            else load_s3(a.bucket, a.site, a.region))
    problems = verify_chain(recs)
    print(f"{len(recs)} records checked")
    for p in problems:
        print("FAIL", p)
    if not problems:
        print("OK: every record matches its hash and links to the previous day")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
