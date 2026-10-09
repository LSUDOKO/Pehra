"""Point the Telegram bot at the deployed API, using the secret token from SSM.

    uv run python scripts/set_webhook.py [--stack invisible-heat]
"""

import argparse
import sys
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parents[1]))

from ihcommon.telegram import Telegram  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stack", default="invisible-heat")
    ap.add_argument("--region", default="ap-south-1")
    ap.add_argument("--prefix", default="/invisible-heat")
    a = ap.parse_args()
    cfn = boto3.client("cloudformation", region_name=a.region)
    stack = cfn.describe_stacks(StackName=a.stack)["Stacks"][0]
    outputs = {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}
    ssm = boto3.client("ssm", region_name=a.region)

    def get(name: str) -> str:
        return ssm.get_parameter(Name=f"{a.prefix}/{name}", WithDecryption=True)["Parameter"]["Value"]

    bot = Telegram(get("telegram-token"))
    bot.set_webhook(outputs["TelegramWebhookUrl"], get("webhook-secret"))
    print(f"webhook set to {outputs['TelegramWebhookUrl']}")


if __name__ == "__main__":
    main()
