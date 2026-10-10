#!/usr/bin/env bash
# Store bot secrets as SSM SecureString (free tier). Never commit these values.
#   TELEGRAM_TOKEN=123:abc ./scripts/setup_secrets.sh   (token optional; keys are generated once)
set -euo pipefail
REGION="${AWS_REGION:-ap-south-1}"
PREFIX="${PARAM_PREFIX:-/invisible-heat}"

put() {  # name value
  aws ssm put-parameter --region "$REGION" --name "$PREFIX/$1" --type SecureString \
    --value "$2" --overwrite >/dev/null
  echo "stored $PREFIX/$1"
}

exists() { aws ssm get-parameter --region "$REGION" --name "$PREFIX/$1" >/dev/null 2>&1; }

if [ -n "${TELEGRAM_TOKEN:-}" ]; then put telegram-token "$TELEGRAM_TOKEN"; else echo "TELEGRAM_TOKEN not set: skipping bot token"; fi
# Generated once; rotating data-key makes stored chat ids unreadable, so keep it.
exists data-key || put data-key "$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
exists webhook-secret || put webhook-secret "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
