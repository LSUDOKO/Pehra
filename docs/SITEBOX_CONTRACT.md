# Pehra Site Box: interface contract

The ESP32 Site Box (Wokwi or real hardware), the server and the 3D digital twin all use these shapes.

## Transport

| Path | Device → server | Server → device |
|---|---|---|
| **AWS IoT Core (primary)** | MQTT publish `pehra/box/{thing}/telemetry` (QoS 0, TLS 8883, X.509 cert) | MQTT `pehra/box/{thing}/cmd` (device subscribes) |
| HTTPS (fallback) | `POST {API}/api/box` with `"token"` in the body | the same JSON returned as the HTTP response |

The twin page polls `GET {API}/api/box/{view_token}/state` every 3 s and is served at `GET {API}/twin/{view_token}`.

## Telemetry (device → server)

```json
{"token": "dev_... (HTTPS only)", "temp_c": 38.5, "rh": 62, "globe_c": 47.0, "light_raw": 3100,
 "tank_distance_cm": 95.0, "drain_distance_cm": 80.0, "sos": false, "fw": "sitebox-1.0"}
```
- `light_raw`: 0–4095 ADC from the LDR divider (higher = brighter sun).
- `tank_distance_cm`: HC-SR04 at the top of the tank (tank height is configured on the server, default 120 cm).
- `drain_distance_cm`: second HC-SR04 above the drain (mount height default 100 cm).
- `sos`: true while the red SOS button was pressed since the last report.

## State / command (server → device and twin)

```json
{"box_id": "box-ab12", "site_name": "Ramesh Tower", "updated_at": "2026-10-11T13:05:00+05:30",
 "readings": {"temp_c": 38.5, "rh": 62, "globe_c": 47.0, "light_pct": 76, "tank_pct": 21, "drain_cm": 20.0},
 "wbgt_c": 33.4, "forecast_wbgt_c": 31.0, "limit_c": 28.2,
 "level": "bahut_zyada", "level_index": 3, "level_label": "BAHUT ZYADA", "color": "#E8282B",
 "rest_minutes": 45, "aaram_now": true, "stop_now": false,
 "fan_on": true, "pump_on": false, "sos_active": false,
 "alerts": ["Tank low"],
 "display": ["WBGT 33.4C BAHUT ZYADA", "45 min aaram/ghanta", "AARAM ABHI", "Tank 21% Naali 20cm"]}
```
- `level_index` 0–4: kam, saavdhaan, zyada, bahut_zyada, khatarnak. `color` per level: `#2FB344`, `#FFC20E`, `#FF8A1F`, `#E8282B`, `#A266B0`.
- `aaram_now`: the device sounds the siren and the twin shows workers resting.
- `fan_on`: mist fan relay. `pump_on`: tank refill relay. `sos_active`: SOS within the last 10 minutes.
- `display`: up to 4 lines of at most 21 ASCII characters for a 128×64 OLED.
