#!/usr/bin/env bash
# Store secrets as SSM SecureString (free tier). Never commit these values. Every value is optional:
#   TELEGRAM_TOKEN=123:abc ./scripts/setup_secrets.sh
#   WHATSAPP_TOKEN=... WHATSAPP_PHONE_ID=... WHATSAPP_APP_SECRET=... ./scripts/setup_secrets.sh
#   TWILIO_SID=AC... TWILIO_TOKEN=... TWILIO_FROM=+1... ./scripts/setup_secrets.sh
set -euo pipefail
REGION="${AWS_REGION:-ap-south-1}"
PREFIX="${PARAM_PREFIX:-/invisible-heat}"

put() {  # name value
  aws ssm put-parameter --region "$REGION" --name "$PREFIX/$1" --type SecureString \
    --value="$2" --overwrite >/dev/null
  echo "stored $PREFIX/$1"
}
exists() { aws ssm get-parameter --region "$REGION" --name "$PREFIX/$1" >/dev/null 2>&1; }
opt() {  # ssm-name env-var
  if [ -n "${!2:-}" ]; then put "$1" "${!2}"; fi
}

# Generated once; rotating data-key makes stored chat ids unreadable, so keep it.
exists data-key || put data-key "$(python3 -c 'import os,base64;print(base64.b64encode(os.urandom(32)).decode())')"
exists webhook-secret || put webhook-secret "$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
exists whatsapp-verify-token || put whatsapp-verify-token "$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"

opt telegram-token TELEGRAM_TOKEN
opt whatsapp-token WHATSAPP_TOKEN
opt whatsapp-phone-id WHATSAPP_PHONE_ID
opt whatsapp-app-secret WHATSAPP_APP_SECRET
opt twilio-sid TWILIO_SID
opt twilio-token TWILIO_TOKEN
opt twilio-from TWILIO_FROM

echo
echo "WhatsApp webhook verify token (paste into the Meta app's Webhooks page):"
aws ssm get-parameter --region "$REGION" --name "$PREFIX/whatsapp-verify-token" --with-decryption \
  --query Parameter.Value --output text
