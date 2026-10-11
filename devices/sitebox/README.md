# Pehra Site Box (ESP32)

One box per worksite. It measures the heat workers actually feel (air, humidity, **black-globe radiant heat**, sun) and the site's water (drinking tank, drain/road flooding). It sends a reading every 10 s. The server sends back what the box should do: the level colour, the rest siren, the mist fan, the tank pump and four lines of OLED text. A red SOS button sends a report straight away.

Interface (telemetry and command JSON): [`docs/SITEBOX_CONTRACT.md`](../../docs/SITEBOX_CONTRACT.md). Server: `functions/iot_box/app.py`, `heatcore/sitebox.py`.

## Files

| File | What |
|---|---|
| `sketch.ino` | Firmware. Config block at the top between `// ==== CONFIG ====` and `// ==== END CONFIG ====` |
| `diagram.json` | Wokwi wiring (all parts, wire colours, demo starts hot) |
| `libraries.txt` | Wokwi / Arduino libraries |
| `secrets_template.h` | Same config names, for real hardware (`secrets.h`, not committed) |

## Parts and what each one does

| Part (Wokwi type) | Job |
|---|---|
| ESP32 DevKitC v4 (`board-esp32-devkit-c-v4`) | WiFi, TLS, runs everything |
| DHT22 (`wokwi-dht22`) | Air temperature and relative humidity (`temp_c`, `rh`) |
| DS18B20 in a matt-black ball (`wokwi-ds18b20`) | Black-globe temperature `globe_c` (radiant heat from sun, tin roofs, concrete), used for measured WBGT = 0.7 Tnw + 0.2 Tg + 0.1 Ta |
| LDR module (`wokwi-photoresistor-sensor`) | Sun brightness `light_raw` 0–4095 (inverted from AO so higher = brighter) |
| HC-SR04 #1 "tank" (`wokwi-hc-sr04`) | Distance from the tank lid to the water, `tank_distance_cm` (server: 120 cm tank by default) |
| HC-SR04 #2 "drain" (`wokwi-hc-sr04`) | Distance to the water in the drain or road, `drain_distance_cm` (server: mounted 100 cm up by default) |
| SSD1306 128×64 OLED (`wokwi-ssd1306`) | Server's 4 `display` lines (size 1) + a 5-segment level bar with the level name; flashes a big **AARAM ABHI** banner while `aaram_now`/`stop_now` |
| 12-pixel NeoPixel ring (`wokwi-led-ring`) | Risk light in `state.color`; breathes faster as `level_index` rises (4 s at kam, 0.4 s at khatarnak); blue while waiting for the server; one white blinking pixel while `sos_active` |
| Buzzer (`wokwi-buzzer`) | Rest siren: 3 beeps when `aaram_now` turns true; a continuous two-tone siren when `stop_now` is true, repeated every 30 s; a short chirp on SOS |
| Red pushbutton "SOS" (`wokwi-pushbutton`) | Debounced; sets `"sos": true` and sends telemetry immediately |
| Relay #1 + cyan LED "FAN" (`wokwi-relay-module`) | Mist fan, follows `fan_on` |
| Relay #2 + blue LED "PUMP" (`wokwi-relay-module`) | Tank refill pump, follows `pump_on` |
| 4.7 kΩ resistor | DS18B20 one-wire pull-up |
| 2 × 220 Ω resistors | LED current limit on the relay outputs |

## Wiring

| Part pin | ESP32 pin | Wire |
|---|---|---|
| DHT22 SDA | GPIO 15 | green |
| DS18B20 DQ (+ 4.7 kΩ to 3V3) | GPIO 4 | yellow |
| LDR module AO | GPIO 34 (ADC1, input-only) | violet |
| Tank HC-SR04 TRIG / ECHO | GPIO 5 / GPIO 18 | orange / blue |
| Drain HC-SR04 TRIG / ECHO | GPIO 17 / GPIO 16 | orange / blue |
| OLED SDA / SCL (I2C 0x3C) | GPIO 21 / GPIO 22 | blue / green |
| NeoPixel ring DIN | GPIO 13 | magenta |
| Buzzer + | GPIO 25 | purple |
| SOS button (other side to GND) | GPIO 32 (INPUT_PULLUP) | gold |
| Fan relay IN | GPIO 26 | cyan |
| Pump relay IN | GPIO 27 | lime |
| Relay COM → NO → LED → 220 Ω → GND | 3V3 on COM | |
| Power | DHT22, DS18B20, OLED, LDR: 3V3. HC-SR04 ×2, ring, relays: 5V. All GND common | red / black |

GPIO 6–11 (flash) are not used; GPIO 34 is the only input-only pin used, as an input.

## Connectivity

1. **AWS IoT Core MQTT (primary).** `WiFiClientSecure` with `setCACert(AWS_ROOT_CA)` (Amazon Root CA 1, already in the sketch), `setCertificate(DEVICE_CERT)`, `setPrivateKey(DEVICE_KEY)`; `PubSubClient` to `IOT_ENDPOINT:8883`, client id = `THING_NAME`, buffer 1024 bytes.
   - publishes telemetry to `pehra/box/<THING_NAME>/telemetry` every 10 s and at once on SOS;
   - subscribes to `pehra/box/<THING_NAME>/cmd` and applies the state JSON.
2. **HTTPS fallback.** Used when `IOT_ENDPOINT` is empty (or the cert/key placeholders are not filled), or when MQTT fails to connect 3 times in a row. `POST {API_URL}/api/box` with `"token": DEVICE_TOKEN`; the response is the same state JSON. This path uses `setInsecure()` (no certificate check); the MQTT path verifies the server.

Serial log lines to look for: `connected, IP …`, `MQTT connected, subscribed …`, `telemetry: {…}`, `telemetry sent (MQTT …)` / `telemetry sent (HTTPS 200)`, `cmd: level=3 BAHUT ZYADA wbgt=33.4 aaram=1 …`, `SOS pressed -> sending now`.

## Run it in Wokwi

1. Open https://wokwi.com/projects/new/esp32.
2. Replace `sketch.ino` and `diagram.json` with the files in this folder.
3. **Library Manager** tab → **+** (Add a new library) → add each line of `libraries.txt`: DHT sensor library for ESPx, OneWire, DallasTemperature, Adafruit SSD1306, Adafruit GFX Library, Adafruit NeoPixel, PubSubClient, ArduinoJson.
4. Fill the CONFIG block (or let the provisioning script do it): `THING_NAME`, `DEVICE_TOKEN`, and for MQTT also `IOT_ENDPOINT`, `DEVICE_CERT`, `DEVICE_KEY`.
5. Press **Play**. The OLED shows the `PEHRA SITE BOX` splash and the connection status, then the server's lines.

The demo starts hot: DHT22 38 °C / 65 %, globe 47 °C, LDR 30 000 lux, tank sonar 100 cm (≈17 % of a 120 cm tank → pump on), drain sonar 80 cm (20 cm of water). Things to try while it runs:
- drag the DS18B20 down to 35 °C → the level falls, the ring slows and changes colour, the fan relay drops;
- drag the tank HC-SR04 to 10 cm → tank full → pump LED off;
- drag the drain HC-SR04 to 40 cm → 60 cm of water → waterlogging alert;
- press **SOS** → immediate report, `sos_active` comes back, the ring shows a blinking white pixel.

With the placeholder `DEVICE_TOKEN` the server answers `{"error": "bad token"}`; the box then shows its own readings on the OLED and keeps retrying, which is enough to check the wiring.

## Real hardware notes

- Put the config in `secrets.h` (from `secrets_template.h`) and replace the CONFIG block with `#include "secrets.h"`.
- HC-SR04 ECHO is 5 V: use a 1 kΩ / 2 kΩ divider into GPIO 18 and 16 (or an HC-SR04P that runs at 3.3 V).
- Most relay boards are active LOW: set `RELAY_ACTIVE_HIGH = false`. Switch the mist fan and pump through the relay contacts, never through the ESP32.
- Globe: a DS18B20 probe in the centre of a 40–150 mm matt-black ball (a painted ping-pong ball is the low-cost version). Let it settle for 10–15 min.
- Keep the DHT22 in shade with airflow (radiation shield); sun on it reads too hot.

## Limits

- MQTT/TLS has not been tested against a live AWS IoT endpoint from inside Wokwi in this repo; the Wokwi-GUEST network passes outbound TCP and the HTTPS fallback is known to work there. If the TLS handshake fails, the box falls back to HTTPS after 3 tries and stays there until reset.
- The HTTPS fallback skips certificate validation (`setInsecure()`); fine for a demo, pin the API certificate for production.
- The server rate-limits HTTPS reports to 12 per minute per device: 10 s reports plus the odd SOS stay under it.
- The natural wet bulb is estimated from air temperature and humidity (Stull); in strong sun the real value runs slightly higher, so the box's WBGT is a lower bound.
