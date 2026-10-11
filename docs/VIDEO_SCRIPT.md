# Pehra: demo video script

Built with Remotion (`video/`), 1920×1080, 30 fps, about 12.5 minutes: the problem first, told fully; then Pehra as four complete stories on a real phone; then the Site Box; then how it runs. Narration: Amazon Polly (Kajal, en-IN). Every number on screen comes from `docs/results/` and the live audit page. The WhatsApp stories play the real phone recording (`scripts/video/phone_cut.py` chapters) inside a phone frame while the narration runs, with the on-screen steps listed beside it.

## Design rules (from the Prompt Motion guidance)
- One accent colour (saffron `#d88b28`) on the website's paper and ink; Inter for Latin, Noto Sans Devanagari for पहरा.
- Springs with a tiny overshoot; no glows, particles, gradients, crossfades or corner text; a recurring saffron dot connects the scenes.
- Every scene has one idea, a source line, and nothing invented: "Research it first; never invent numbers."

## Narration by scene

| Act | Scene | Length | Narration |
|---|---|---|---|
| 1 · The problem | `open` | 7 s | Every summer, India measures heat with a thermometer. But a thermometer cannot feel what a body feels. |
| 1 · The problem | `humidity` | 11 s | The body cools itself by sweating. On a humid day, sweat does not dry, and the cooling stops. So a humid 36 degree day can hurt a worker more than a dry 42 degree day. |
| 1 · The problem | `wbgt` | 14 s | Safety scientists measure this with W B G T: one number that combines temperature, humidity, sun and wind. It is what the US and many armies use to decide when work must stop. India's public heat alerts still use temperature alone. |
| 1 · The problem | `kharghar` | 16 s | 16 April 2023, Kharghar, near Mumbai. People died of heatstroke at an open-air event. The maximum temperature that day was 38.8 degrees. Under the official rule, that is not a heatwave. No alert. |
| 1 · The problem | `kharghar_wbgt` | 15 s | We replayed that day with weather reanalysis data. W B G T in the sun crossed the safe limit for moderate work from ten in the morning to four in the afternoon, peaking at 30.8 degrees at noon. The danger was real. It was just invisible. |
| 1 · The problem | `audit` | 28 s | So we checked how often this happens. Twelve cities, five years, 2021 to 2025. 4,372 city-days crossed the W B G T work limit while no heatwave was declared. That is 97 percent of all such days. 2,327 of them fell outside March to June, when heatwave bulletins do not even run. These are published on the Pehra audit page, with the method and every caveat. |
| 1 · The problem | `water` | 8 s | The same years held 90 days of heavy rain and 68 warm nights, when the body cannot recover at night. Heat and water are one problem. |
| 2 · Pehra on WhatsApp | `intro` | 12 s | Pehra means guard. It is a heat and water guard that lives on WhatsApp, in Hindi, with no app to install. It turns the free weather forecast into W B G T, and W B G T into a plan for the day. |
| 2 · Pehra on WhatsApp | `story_supervisor` | 14 s | The first story. Ramesh runs a construction site in Kharghar. On a real phone, he registers the site and types his crew in plain Hindi: forty people, ten on heavy work, three new. Pehra reads it back, and he confirms. |
| 2 · Pehra on WhatsApp | `story_supervisor_plan` | 15 s | Every evening at seven, he gets tomorrow's plan: when to stop work, how many minutes of rest each hour, how much water to stock. It comes as text and as a Hindi voice note. He approves it with one tap, and the plan is saved to a tamper-proof record. |
| 2 · Pehra on WhatsApp | `story_worker` | 19 s | The second story. Gurpreet works on that site. He scans the site QR code. No app, no login. He logs his rest break. If he feels dizzy, he taps chakkar, and sees fixed first aid. At that moment Ramesh gets a WhatsApp alert, and his phone rings with a Hindi call. |
| 2 · Pehra on WhatsApp | `story_ask` | 14 s | Ramesh can also just ask. Can we pour concrete at two tomorrow? Pehra answers from the plan's own numbers: no, heavy work is stopped then. The AI explains, but it never does the maths, and it can never loosen a limit. |
| 2 · Pehra on WhatsApp | `story_family` | 18 s | The third story. Meena is expecting, and lives with her small son and her mother-in-law in Mumbai. She says hi, answers five button questions about her household, counts only, never names, and gets today's plan with stricter limits for the vulnerable. On dangerous days, Dadi gets a Hindi phone call. |
| 2 · Pehra on WhatsApp | `story_vendor` | 14 s | The fourth story. Lakshmi sells fruit on a Delhi street. She types paani, Connaught Place, and gets the nearest drinking water, 190 metres away, with a map link. Schools and delivery riders get their own plans too. |
| 3 · The Site Box | `box_why` | 5 s | Some sites have no smartphone at all. For them, Pehra is a box. |
| 3 · The Site Box | `box_what` | 21 s | The Pehra Site Box is about 600 rupees of parts around an E S P 32. A humidity sensor reads the air. A probe inside a matt black globe reads the heat of the sun and the concrete. Together they give the real W B G T on that site, every ten seconds. Two sonar sensors watch the drinking water tank and the drain. |
| 3 · The Site Box | `box_does` | 15 s | The box does not just measure. It acts. The ring shows the risk colour. A siren rings when it is time to rest. A relay turns on a mist fan. Another refills the tank. And a red button calls for help. |
| 3 · The Site Box | `box_sim` | 16 s | Here it is running in the Wokwi simulator, with the real firmware. The readings go to AWS IoT Core over a secure certificate. A rule hands them to a Lambda function, which computes W B G T, applies the plan, and publishes the command back to the box. |
| 3 · The Site Box | `box_twin` | 15 s | Every box gets a live 3D twin on the web. The twin shows what the box sees: the risk, the rest, the tank, the fan, the pump. When the SOS button is pressed, the twin turns red, the supervisor gets a WhatsApp alert, and a Hindi call. |
| 4 · How it runs | `arch` | 22 s | Under the hood, Pehra is one serverless stack on AWS, in Mumbai. The forecast becomes W B G T once per city, so a million sites cost the same as one. Step Functions waits for the supervisor's approval. Amazon Bedrock explains the plan, Cedar policy makes sure the AI can never loosen it, Polly speaks Hindi, and every day's record is locked in S3. |
| 4 · How it runs | `honest` | 11 s | What Pehra does not claim: it does not save lives, and it is not medical advice. It is designed to reduce exposure, and every number it sends comes from code, never from the model. |
| 4 · How it runs | `outro` | 6 s | Pehra. A guard for the heat you cannot see. Built on AWS by Team Mavricks. |

## Footage
- Phone: `out/video/raw/phone_1.mp4` (scrcpy, moto g34, 11 Oct 2026) → chapters in `out/video/phone/` (number blurred; waits sped up and labelled; call audio = the Polly MP3 the call played).
- Wokwi: `out/video/wokwi.mp4` (real firmware, simulated hardware). Twin: `out/video/twin.mp4` via `scripts/video/record_twin.mjs`.
- Illustrations: Codex-generated, brand style, `video/public/gen/`.

## Honesty labels on screen
"Real phone recording · WhatsApp test number · Twilio trial call", "Wokwi ESP32 simulator · real firmware · simulated hardware", "readings published to IoT Core from a laptop script for the demo", "not 'saves lives', not medical advice".
