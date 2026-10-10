# Site sensors: ESP32 + DHT22 + HC-SR04 (real, Wokwi, or web simulator)

A weather grid is 11–25 km wide. A tin-roofed site, a concrete yard or a flooded lane is not. A ₹500 sensor closes that gap. There are three ways to run it, all posting to the same API (`POST /api/sensor`) with a per-device token:

| Option | Cost | What you need |
|---|---|---|
| **Web simulator** | Free | Open the link the bot gives you: `https://<api>/device/<token>` |
| **Wokwi** (free online ESP32 simulator; its virtual WiFi reaches the internet) | Free | wokwi.com, no hardware |
| **Real hardware** | About ₹600 (ESP32, DHT22, HC-SR04, LED, buzzer) | WiFi at the site |

## What each reading becomes

| Device (`/device …`) | Reading | Server does | Alert to supervisor or household |
|---|---|---|---|
| `weather` | temp °C, RH % | Site-corrected WBGT: measured air plus forecast wind and sun for this hour (Liljegren) | Site is ≥ 1 °C WBGT hotter than the forecast (at most once every 3 h) |
| `tank 120` | distance to the water (cm) | % full for a 120 cm tank | Below 20%, with today's 20 L can order for sites (at most once every 6 h) |
| `drain 100` | distance to the water (cm) | Water depth below a sensor mounted 100 cm above the drain | ≥ 30 cm: waterlogging text, plus a Hindi phone call if the site opted in with `/call_on` (at most once an hour) |

The response tells the device `"alert": true/false`; the ESP32 lights its red LED and sounds the buzzer. Every reading is checked by Cedar (`device-post-own-stream`): a device token can only write to the site or household it was created for. Readings expire after 7 days.

## Wokwi in 3 minutes

1. In the bot: `/device weather` and `/device tank 120` (or `/device drain 100`). Copy the two `dev_…` tokens.
2. Open https://wokwi.com/projects/new/esp32. Replace `sketch.ino` and `diagram.json` with the files in this folder. In the Library Manager add **DHT sensor library for ESPx**.
3. Paste the tokens into `WEATHER_TOKEN` and `LEVEL_TOKEN`, then press **Play**.
4. Click the DHT22 and drag the temperature to 40 °C and the humidity to 70%. Click the HC-SR04 and drag the distance (a long distance means an empty tank). Within 15 s the serial monitor shows the API's answer, the LED lights up, and the phone gets the alert.

## Wiring (same on real hardware)

| Part | ESP32 pin |
|---|---|
| DHT22 data | GPIO 15 (VCC 3.3 V, GND) |
| HC-SR04 TRIG / ECHO | GPIO 5 / GPIO 18 (VCC 5 V, GND; use a divider on ECHO for real boards) |
| Red LED (220 Ω) | GPIO 2 |
| Buzzer | GPIO 4 |

## Limits

- DHT22 accuracy is about ±0.5 °C and ±2–5% RH. Keep it in shade with airflow (a radiation shield); direct sun on the sensor reads too hot.
- No globe thermometer, so radiant heat comes from the forecast. A black-globe probe (DS18B20 in a painted ball) is the next upgrade.
- The demo firmware skips TLS certificate pinning (`setInsecure()`); pin the certificate for production.
