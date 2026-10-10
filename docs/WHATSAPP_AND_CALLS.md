# WhatsApp and Hindi voice-call alerts (free demo setup)

Both work on free test or trial accounts and are meant for the demo video. Telegram stays the
always-free main channel. Label both on screen: "WhatsApp test number" and "Twilio trial call".

## What works for free

| | Works | Limit on the free setup |
|---|---|---|
| WhatsApp (Meta Cloud API test number) | Plan text, Hindi voice note, Approve/Override buttons, Q&A, voice crew roster, `/call_on` with your own number | Up to 5 recipient numbers you add in the Meta app. Messages only within 24 h of the supervisor's last message, so send `plan` first. The 19:00 push outside that window is dropped (`WhatsAppOutsideWindow` metric); it would need a paid utility template. |
| Voice call (Twilio free trial) | Fixed Hindi alert spoken by Polly (Kajal), played twice: symptom report, stop-work re-check, `/test_call` | Calls only numbers verified in Twilio (up to 5). A short "trial account" notice plays first. The caller ID is a Twilio number. The trial ends after 30 days or when the credit runs out. |

## 1. WhatsApp (about 10 minutes)

1. Go to developers.facebook.com, then My Apps, then Create app (type "Business"), then add the **WhatsApp** product.
2. Under WhatsApp, open **API Setup**. Note the **Phone number ID** and the **temporary access token**, which lasts 24 h. For a longer-lived token, create a System User token with `whatsapp_business_messaging`.
3. In the same screen, add your phone (and your teammate's) under **To** and verify it with the code.
4. Under App settings, then Basic, note the **App secret**.
5. Store the values (also generates the webhook verify token):
   ```bash
   WHATSAPP_TOKEN=... WHATSAPP_PHONE_ID=... WHATSAPP_APP_SECRET=... ./scripts/setup_secrets.sh
   ```
6. Under WhatsApp, open **Configuration**, then Webhook:
   - Callback URL: the `WhatsAppWebhookUrl` stack output (`https://<api>/whatsapp`)
   - Verify token: printed by the script above
   - Subscribe to the **messages** field.
7. From your phone, message the test number: `hi`, then `/register Ramesh Tower, Chennai`, `/crew 40 10 3`, `plan`.

## 2. Hindi voice calls (about 5 minutes)

1. Sign up for a free trial at twilio.com and verify your own phone number (SMS).
2. Get a trial phone number in the console. Note the **Account SID** and **Auth Token**.
3. Store them:
   ```bash
   TWILIO_SID=AC... TWILIO_TOKEN=... TWILIO_FROM=+1XXXXXXXXXX ./scripts/setup_secrets.sh
   ```
4. In the bot (Telegram or WhatsApp): `/call_on +91XXXXXXXXXX` (on WhatsApp, `/call_on` alone uses your own number), then `/test_call`.

When calls happen (only after `/call_on`):
- A worker taps **Chakkar aa raha hai** on the QR page. The supervisor gets the text alert **and** a phone call.
- The midday re-check makes the plan stricter and there is a stop-work window. A text alert and a call go out. For the demo: `aws lambda invoke --function-name <RecheckFunctionName> --payload '{"simulate_delta_c": 1.5}' out.json`. The call says it is a simulated forecast.

## Demo video sequence

1. WhatsApp: `plan` → the Hindi plan with Approve/Override buttons, then the voice note → tap Approve.
2. Send a voice note: "40 log, 10 bhaari kaam, 3 naye aaye" → the read-back → Haan, sahi.
3. Ask: "Kya hum 2 baje concrete daal sakte hain?"
4. Phone: scan the poster QR → tap Chakkar aa raha hai → the WhatsApp alert arrives and the phone rings with the Hindi call.
5. On screen: "WhatsApp test number · Twilio trial call · simulated forecast".

## Privacy

Phone numbers for calls are stored only after `/call_on`, AES-GCM encrypted, and removed by `/call_off` or `/delete_my_data`. Call audio is fixed text. The MP3 is served through a 15-minute presigned URL and deleted after 1 day.
