# Pehra · Invisible Heat: demo video script (about 14 minutes)

Recorded, 1920×1080, 30 fps. Voice-over: Amazon Polly (Kajal, neural, en-IN and hi-IN). Characters are from `Pehra_Character_Sheets/` (illustrations, not real people). Every number on screen comes from the project's own data (`docs/results/`). Simulated parts are labelled on screen.

| # | Time | Scene | Visuals | Voice-over |
|---|---|---|---|---|
| 1 | 0:00–0:12 | **Cold open** | Peach sky. Garmi slides in arms crossed, the title "INVISIBLE HEAT" slams in, Boondi waves. "PEHRA" badge. | "Every summer, India warns its people with a thermometer. But the heat that hurts is invisible." |
| 2 | 0:12–0:32 | **Kharghar, 16 April 2023** | A date card, then real ERA5 numbers: max 38.8 °C, "IMD rule: no heatwave". Hourly WBGT bars rise past the 28.2 °C NIOSH line and the 10:00–14:00 event window lights red. | "On 16 April 2023, people died of heatstroke at an open-air event in Kharghar. The temperature was 38.8 degrees, below any heatwave alarm. But heat and humidity together, WBGT, crossed the safe-work limit for hours." |
| 3 | 0:32–0:48 | **The audit** | A counter runs up to 4,372; city bars grow (12 cities, 2021–2025); chips for 2,327 days outside March–June, 90 heavy-rain days and 68 warm nights. "A minimum" caveat. | "We audited twelve Indian cities over five years. 4,372 days crossed the WBGT limit with no heatwave declared, half of them outside the heatwave season. And the water side too: heavy rain and hot nights." |
| 4 | 0:48–1:32 | **Meet the people** | Eight character vignettes, about 5 s each, with Boondi helping. Each shows a real bot message bubble. | One line per character, below |
| 5 | 1:32–1:57 | **Pehra Site Box** | The Wokwi ESP32 (real simulation screenshots) with callouts for the DHT22, globe probe, sonar, OLED, light, siren, SOS, fan and pump. Cut to the live 3D twin GIF. "SIMULATED HARDWARE · WOKWI" label. | "For sites with no smartphone, a six-hundred-rupee Pehra Site Box measures real WBGT with a black-globe sensor, rings a rest siren every hour, turns on mist fans, refills the water tank and sends an SOS. It runs on AWS IoT Core, and every site gets a live 3D twin." |
| 6 | 1:57–2:22 | **How AWS runs it** | An animated architecture: data packets flow from Open-Meteo → EventBridge → Lambda → S3 heat store; WhatsApp → API Gateway → Lambda → Step Functions → Bedrock with Strands → Polly → SQS → WhatsApp; IoT Core → Lambda → DynamoDB; S3 Object Lock records. A Cedar shield blocks "AI: loosen plan". | "Under the hood it is all serverless on AWS. The forecast becomes WBGT once per city, so a million sites cost the same as one. Step Functions waits for the supervisor's approval. Amazon Bedrock with Strands explains the plan, but tools do the maths, and Cedar makes sure the AI can never loosen a safety limit." |
| 7 | after the Site Box | **Live on WhatsApp** (real phone recording, 17 chapters, below) | A real phone screen recording via scrcpy: `hi` → family plan → `paani` → nearest water → `call` → the phone rings with the Hindi call → the worker QR "Chakkar" alert. "WhatsApp test number · Twilio trial" label. | "And it lives where people already are: WhatsApp, in Hindi, with voice notes and phone calls. No app to install." |
| 8 | 2:47–2:58 | **Outro** | Every character lines up, Boondi raises a glass, Garmi sulks on a cloud. "Stay cool, India." Links, "Built on AWS", team Mavricks. | "Pehra. Making invisible heat visible, and acting on it. Stay cool, India." |

## WhatsApp chapters (real phone, moto g34, 11 Oct 2026)

Cut from one scrcpy recording by `scripts/video/phone_cut.py`. Each chapter: the phone clip, a title, what it shows, and a timed "on the phone now" step list. Waits are sped up and say so; the owner's number is blurred; call audio is the same Polly MP3 the call played; tokens seen on screen were rotated afterwards.

| # | Chapter | Shows |
|---|---|---|
| 1 | Say hi on WhatsApp | No app to install: Pehra is a WhatsApp number, Choose: site, school, shop, or me and my family |
| 2 | Five taps build the family profile | Elderly, under-5s, pregnancy, illness, outdoor work, Counts only, never names |
| 3 | Today's plan for Mumbai, in Hindi | From this morning's Open-Meteo forecast, Khatarnak: vulnerable people indoors 9 to 5, Best hours for errands, and 108 if unwell |
| 4 | "paani Connaught Place" | Nearest drinking water: 190 m, with a map link, OpenStreetMap points plus community reports, Send a location pin or type a landmark |
| 5 | A supervisor registers a site | /register Ramesh Tower, Kharghar, Construction, school, shop or delivery rider |
| 6 | The crew, in plain Hindi | "40 log, 10 bhaari kaam, 3 naye aaye", Read back before saving, /call_on: Hindi call alerts to this phone |
| 7 | Tomorrow's plan + a Hindi voice note | Stop work 9 to 5, rest bands around it, Heavy work stopped, new workers at 20%, 7 water cans · Approve or Override |
| 8 | Worker QR page + printable poster | One link per site, printed as a QR code, Workers need no app and no login |
| 9 | A worker taps "chakkar" | Aaram shuru logs a rest break, Chakkar aa raha hai shows fixed first aid, The supervisor is told at once |
| 10 | The supervisor's alert | When, and how many reports in the last hour, First aid and 108: fixed text, never AI |
| 11 | A Hindi phone call | Amazon Polly Hindi voice, played by Twilio, Trial account: a short notice plays first, You hear the exact audio the call played |
| 12 | Ask anything | "Kya hum kal dopahar 2 baje concrete daal sakte hain?", Bedrock (Nova Pro) + Strands, answers from tools, A number check blocks invented numbers |
| 13 | Dadi gets a call on dangerous days | /family_call adds an elder's number (blurred here), Today is khatarnak, so one Hindi call goes out, Stay inside 9 to 5, sip water, 108 |
| 14 | The Site Box joins from WhatsApp | /device box: box id, device token, 3D twin link, Readings over AWS IoT Core (here from a laptop script), Alerts: hotter than forecast, tank low, pump on |
| 15 | The live 3D twin, on the phone | Measured WBGT 34.2 °C: khatarnak, kaam band, Tank refilling, mist fan on, Updates every 3 s from the box state |
| 16 | SOS from the site | The red SOS button on the box, The twin turns red, WhatsApp alert, Hindi call |
| 17 | Only the supervisor can loosen a plan | Override, Dheela, and a written reason, Cedar policy: never the AI, The reason is saved to the record |

## Scene 4 lines (character → feature)

| Character (pose) | Feature shown | Voice-over |
|---|---|---|
| Ramesh, site supervisor (phone, voice note) | 7 pm Hindi plan + voice + Approve | "Ramesh gets tomorrow's plan at 7 pm as a Hindi voice note: when to stop work, how much rest, how much water." |
| Gurpreet, construction worker (QR → shade) | Worker QR page, rest log | "Gurpreet scans the site QR to log his rest. No app, no login." |
| Bhanwari, brick-kiln worker (sun → shade with matka) | Hourly rest bands | "Bhanwari's crew rests in the shade before the heat peaks, not after someone collapses." |
| Arjun, delivery rider (phone → drinking water) | Rider break windows | "Arjun gets break windows built for riders." |
| Lakshmi, street vendor (phone → points to tap) | "Paani kahan" water finder | "Lakshmi asks 'paani kahan' and finds the nearest drinking water." |
| Dadi, grandmother (phone call) | Family Hindi call | "On dangerous days, Dadi gets a phone call in Hindi telling her to stay inside." |
| Meena and Chotu (family plan) | Family mode, stricter limits | "Meena's family plan uses stricter limits for her child and her pregnancy." |
| Ms Fernandes, principal (school) | School mode | "And Ms Fernandes moves assembly indoors." |

## Honesty rules on screen
- "Designed to reduce exposure": never "saves lives", never "safe".
- Kharghar: "no official heatwave warning", plus the ERA5 numbers. No claim that anyone would have been saved.
- Labels: "Illustrated characters", "Simulated hardware (Wokwi)", "WhatsApp test number", "Twilio trial call".

## Production
- Built by code: `scripts/video/build_video.py` (scenes in `scenes.py`, drawing kit in `kit.py`). The final voice-over text is the `VO` table in `scenes.py`; scene lengths follow the Polly audio, so the cut is about 14 minutes (no length cap; the WhatsApp walkthrough is the main part).
- Characters: `scripts/video/cut_characters.py` cuts `Pehra_Character_Sheets/` into transparent poses (`out/video/chars/`). Poses with scene art get feathered edges.
- Chat bubbles are produced by the bot's own templates (`heatcore/templates_hi.py`, `templates_people.py`) for the Kharghar ERA5 day, and the water reply uses cached OpenStreetMap points near Connaught Place, Delhi. The corner label says "illustrated characters · real bot text".
- Audio: Polly neural Kajal (en-IN), loudness-normalised to -15 LUFS, a quiet generated music bed ducked under the voice, soft whooshes on the wipes. Subtitles are burned in and also written as `.srt`.
- Footage: `out/video/wokwi.mp4` and `out/video/twin.mp4` (screen recordings of the Wokwi run and the live twin) are overlaid in scene 5 when present; otherwise stills are used.
- Scene 7: `scripts/video/record_phone.sh` (scrcpy) records `out/video/phone.mp4`; the next build places it in the phone frame and mixes its audio. Without it, the scene shows a recreated chat built from real bot replies, labelled as such.
- Outputs: `out/video/pehra_demo.mp4`, `.srt`, `thumbnail.jpg` (1280×720) and `chapters.txt` for the YouTube description.

```bash
uv run python scripts/video/cut_characters.py
uv run python scripts/video/build_video.py --stills     # spot-check frames in out/video/stills/
uv run python scripts/video/build_video.py              # full render, about 5 min on 12 cores
```
