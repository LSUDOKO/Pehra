"""Monthly compliance PDF for one site, built from its locked records in S3.

Invoke with {"site_id": "...", "month": "2026-10"}; returns a 1-hour presigned link.
Cedar: only the site's supervisor or a contractor of the same tenant may read records.
"""

import json

import boto3

from ihcommon import authz, config, repo
from ihcommon.report import build_pdf


def handler(event, _ctx):
    t = repo.table()
    site = repo.get_site(t, event["site_id"])
    if not site:
        return {"error": "unknown site"}
    principal = event.get("principal") or {"type": "Supervisor", "id": site["owner_hash"]}
    record = authz.entity("Record", f"{site['site_id']}#{event['month']}",
                          site=authz.uid("Site", site["site_id"]))
    ents = authz.site_entities(site) + [record]
    if principal["type"] == "Contractor":
        ents.append(authz.entity("Contractor", principal["id"], tenant=principal.get("tenant", "")))
    if not authz.authorize(principal, "ReadRecord", record["uid"], ents):
        return {"error": "forbidden"}
    s3 = boto3.client("s3", region_name=config.REGION)
    prefix = f"records/{site['site_id']}/{event['month']}"
    keys = [o["Key"] for page in s3.get_paginator("list_objects_v2").paginate(
        Bucket=config.RECORDS_BUCKET, Prefix=prefix) for o in page.get("Contents", [])]
    recs = [json.loads(s3.get_object(Bucket=config.RECORDS_BUCKET, Key=k)["Body"].read()) for k in keys]
    if not recs:
        return {"error": "no records for that month"}
    key = f"reports/{site['site_id']}/{event['month']}.pdf"
    s3.put_object(Bucket=config.MEDIA_BUCKET, Key=key, Body=build_pdf(recs, site["name"]),
                  ContentType="application/pdf")
    url = s3.generate_presigned_url("get_object", Params={"Bucket": config.MEDIA_BUCKET, "Key": key},
                                    ExpiresIn=3600)
    return {"records": len(recs), "url": url}
