# Pehra · Invisible Heat: demo video script (2:58)

Recorded, 1920×1080, 30 fps. Voice-over: Amazon Polly (Kajal, neural, en-IN and hi-IN). Characters are from `Pehra_Character_Sheets/` (illustrations, not real people). Every number on screen comes from the project's own data (`docs/results/`). Simulated parts are labelled on screen.

| # | Time | Scene | Visuals | Voice-over |
|---|---|---|---|---|
| 1 | 0:00–0:12 | **Cold open** | Peach sky. Garmi slides in arms crossed, the title "INVISIBLE HEAT" slams in, Boondi waves. "PEHRA" badge. | "Every summer, India warns its people with a thermometer. But the heat that hurts is invisible." |
| 2 | 0:12–0:32 | **Kharghar, 16 April 2023** | A date card, then real ERA5 numbers: max 38.8 °C, "IMD rule: no heatwave". Hourly WBGT bars rise past the 28.2 °C NIOSH line and the 10:00–14:00 event window lights red. | "On 16 April 2023, people died of heatstroke at an open-air event in Kharghar. The temperature was 38.8 degrees, below any heatwave alarm. But heat and humidity together, WBGT, crossed the safe-work limit for hours." |
| 3 | 0:32–0:48 | **The audit** | A counter runs up to 4,372; city bars grow (12 cities, 2021–2025); chips for 2,327 days outside March–June, 90 heavy-rain days and 68 warm nights. "A minimum" caveat. | "We audited twelve Indian cities over five years. 4,372 days crossed the WBGT limit with no heatwave declared, half of them outside the heatwave season. And the water side too: heavy rain and hot nights." |
| 4 | 0:48–1:32 | **Meet the people** | Eight character vignettes, about 5 s each, with Boondi helping. Each shows a real bot message bubble. | One line per character, below |
| 5 | 1:32–1:57 | **Pehra Site Box** | The Wokwi ESP32 (real simulation screenshots) with callouts for the DHT22, globe probe, sonar, OLED, light, siren, SOS, fan and pump. Cut to the live 3D twin GIF. "SIMULATED HARDWARE · WOKWI" label. | "For sites with no smartphone, a six-hundred-rupee Pehra Site Box measures real WBGT with a black-globe sensor, rings a rest siren every hour, turns on mist fans, refills the water tank and sends an SOS. It runs on AWS IoT Core, and every site gets a live 3D twin." |
| 6 | 1:57–2:22 | **How AWS runs it** | An animated architecture: data packets flow from Open-Meteo → EventBridge → Lambda → S3 heat store; WhatsApp → API Gateway → Lambda → Step Functions → Bedrock with Strands → Polly → SQS → WhatsApp; IoT Core → Lambda → DynamoDB; S3 Object Lock records. A Cedar shield blocks "AI: loosen plan". | "Under the hood it is all serverless on AWS. The forecast becomes WBGT once per city, so a million sites cost the same as one. Step Functions waits for the supervisor's approval. Amazon Bedrock with Strands explains the plan, but tools do the maths, and Cedar makes sure the AI can never loosen a safety limit." |
| 7 | 2:22–2:47 | **Live on WhatsApp** (phone recording) | A real phone screen recording via scrcpy: `hi` → family plan → `paani` → nearest water → `call` → the phone rings with the Hindi call → the worker QR "Chakkar" alert. "WhatsApp test number · Twilio trial" label. | "And it lives where people already are: WhatsApp, in Hindi, with voice notes and phone calls. No app to install." |
| 8 | 2:47–2:58 | **Outro** | Every character lines up, Boondi raises a glass, Garmi sulks on a cloud. "Stay cool, India." Links, "Built on AWS", team Mavricks. | "Pehra. Making invisible heat visible, and acting on it. Stay cool, India." |

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
- Auto-generated by `scripts/video/build_video.py`: scenes 1–6 and 8, the voice-over, music-free mix and burned-in subtitles.
- Scene 7 comes from the phone: `scrcpy --record out/video/phone.mp4`, then rebuild with `--phone out/video/phone.mp4`.
- Output: `out/video/pehra_demo.mp4` (upload to YouTube; under 3:00).
