"""Provision a Pehra Site Box as an AWS IoT Core thing and write a ready-to-paste Wokwi sketch.

    uv run python scripts/iot_provision.py --box box-abc123 --device-token dev_... [--stack invisible-heat]

Creates the thing (name = box id), an active X.509 certificate, attaches the stack's IoT policy, and
fills the CONFIG block of devices/sitebox/sketch.ino. Certificates and the filled sketch go to
out/iot/<box>/ (gitignored) - never commit them.
"""

import argparse
import re
import sys
from pathlib import Path

import boto3

ROOT = Path(__file__).parents[1]


def fill(sketch: str, values: dict) -> str:
    for name in ("THING_NAME", "IOT_ENDPOINT", "API_URL", "DEVICE_TOKEN"):
        sketch, n = re.subn(rf'(const char\*\s+{name}\s*=\s*)"[^"]*"', rf'\g<1>"{values[name]}"', sketch)
        if n == 0:
            raise SystemExit(f"sketch has no {name} constant")
    for name in ("DEVICE_CERT", "DEVICE_KEY"):
        sketch, n = re.subn(rf'({name}\[\]\s*PROGMEM\s*=\s*R"EOF\().*?(\)EOF")', lambda m, v=values[name]: m.group(1) + v.strip() + m.group(2),
                            sketch, flags=re.S)
        if n == 0:
            raise SystemExit(f"sketch has no {name} block")
    return sketch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", required=True)
    ap.add_argument("--device-token", default="")
    ap.add_argument("--stack", default="invisible-heat")
    ap.add_argument("--region", default="ap-south-1")
    a = ap.parse_args()
    cfn = boto3.client("cloudformation", region_name=a.region)
    outputs = {o["OutputKey"]: o["OutputValue"] for o in cfn.describe_stacks(StackName=a.stack)["Stacks"][0]["Outputs"]}
    iot = boto3.client("iot", region_name=a.region)
    try:
        iot.create_thing(thingName=a.box)
    except iot.exceptions.ResourceAlreadyExistsException:
        pass
    cert = iot.create_keys_and_certificate(setAsActive=True)
    iot.attach_policy(policyName=outputs["SiteBoxIotPolicyName"], target=cert["certificateArn"])
    iot.attach_thing_principal(thingName=a.box, principal=cert["certificateArn"])
    endpoint = iot.describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]

    out = ROOT / "out" / "iot" / a.box
    out.mkdir(parents=True, exist_ok=True)
    (out / "device.pem.crt").write_text(cert["certificatePem"])
    (out / "private.pem.key").write_text(cert["keyPair"]["PrivateKey"])
    (out / "private.pem.key").chmod(0o600)
    sketch = (ROOT / "devices/sitebox/sketch.ino").read_text()
    filled = fill(sketch, {"THING_NAME": a.box, "IOT_ENDPOINT": endpoint, "API_URL": outputs["ApiUrl"],
                           "DEVICE_TOKEN": a.device_token, "DEVICE_CERT": cert["certificatePem"],
                           "DEVICE_KEY": cert["keyPair"]["PrivateKey"]})
    (out / "sketch.ino").write_text(filled)
    print(f"thing: {a.box}\nendpoint: {endpoint}\ncertificate: {cert['certificateId'][:12]}...")
    print(f"ready-to-paste Wokwi sketch: {out / 'sketch.ino'}  (contains the private key - do not share)")


if __name__ == "__main__":
    sys.exit(main())
