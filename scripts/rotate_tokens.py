"""Rotate leaked tokens: a site's worker-page token (QR / poster links) and a Site Box's device token.

    uv run python scripts/rotate_tokens.py --site site-ab12cd34      # old QR and poster links stop working
    uv run python scripts/rotate_tokens.py --box box-5rbzggdb        # old device token is rejected

The supervisor gets the new site links with "links" on WhatsApp. The new device token is printed once:
put it in the box's sketch (DEVICE_TOKEN) or run scripts/iot_provision.py again.
"""

import argparse

import boto3
from boto3.dynamodb.conditions import Attr

from ihcommon import config, crypto, repo


def rotate_site(t, site_id: str) -> None:
    site = repo.get_site(t, site_id)
    if not site:
        raise SystemExit(f"no site {site_id}")
    old, new = site["site_token"], crypto.new_site_token()
    t.put_item(Item={"PK": f"TOKEN#{new}", "SK": "META", "site_id": site_id})
    t.update_item(Key={"PK": f"SITE#{site_id}", "SK": "META"}, UpdateExpression="SET site_token = :n",
                  ExpressionAttributeValues={":n": new})
    t.delete_item(Key={"PK": f"TOKEN#{old}", "SK": "META"})
    print(f"{site_id}: worker-page token rotated; send 'links' in the bot for the new QR and poster")


def rotate_box(t, box_id: str, key: str) -> None:
    if not t.get_item(Key={"PK": f"BOX#{box_id}", "SK": "META"}).get("Item"):
        raise SystemExit(f"no box {box_id}")
    old, kw = [], {"FilterExpression": Attr("box_id").eq(box_id) & Attr("PK").begins_with("BOXDEV#")}
    while True:
        page = t.scan(**kw)
        old += [it["PK"] for it in page["Items"]]
        if "LastEvaluatedKey" not in page:
            break
        kw["ExclusiveStartKey"] = page["LastEvaluatedKey"]
    dev = "dev_" + crypto.new_site_token()
    t.put_item(Item={"PK": f"BOXDEV#{crypto.keyed_hash(dev, key)}", "SK": "META", "box_id": box_id})
    for pk in old:
        t.delete_item(Key={"PK": pk, "SK": "META"})
    print(f"{box_id}: {len(old)} old device token(s) revoked. New DEVICE_TOKEN (shown once): {dev}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", action="append", default=[])
    ap.add_argument("--box", action="append", default=[])
    args = ap.parse_args()
    t = boto3.resource("dynamodb", region_name=config.REGION).Table(config.TABLE)
    key = config.param("data-key") if args.box else ""
    for sid in args.site:
        rotate_site(t, sid)
    for bid in args.box:
        rotate_box(t, bid, key)


if __name__ == "__main__":
    main()
