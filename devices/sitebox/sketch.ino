// ==== CONFIG ====
// Filled in by the provisioning script (or by hand). Keep the names exactly as they are.
const char* THING_NAME = "pehra-box-demo";            // AWS IoT thing name = MQTT client id
const char* IOT_ENDPOINT = "";                        // e.g. "abcd1234-ats.iot.ap-south-1.amazonaws.com"; empty = HTTPS only
const char* API_URL = "https://yj61i9i7g0.execute-api.ap-south-1.amazonaws.com";
const char* DEVICE_TOKEN = "PASTE_DEVICE_TOKEN";      // "dev_..." token for the HTTPS fallback
const char AWS_ROOT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----
)EOF";
const char DEVICE_CERT[] PROGMEM = R"EOF(
PASTE_DEVICE_CERTIFICATE_PEM_HERE
)EOF";
const char DEVICE_KEY[] PROGMEM = R"EOF(
PASTE_DEVICE_PRIVATE_KEY_PEM_HERE
)EOF";
// ==== END CONFIG ====

// Pehra Site Box - ESP32 heat-and-water station for one worksite.
// Sensors: DHT22 (air temp, RH), DS18B20 in a black globe (radiant heat), LDR (sun),
// HC-SR04 x2 (drinking-water tank level, drain/road water level), red SOS button.
// Outputs: SSD1306 OLED (server's 4 display lines + level bar), 12-pixel NeoPixel ring (risk colour,
// pulses faster as the level rises), buzzer (rest siren), relay 1 = mist fan, relay 2 = tank pump.
// Transport: AWS IoT Core MQTT over TLS (X.509) first; HTTPS POST {API_URL}/api/box as fallback.
// Contract: docs/SITEBOX_CONTRACT.md. Runs on real hardware or free in Wokwi (wokwi.com).

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>
#include "DHTesp.h"

const char* WIFI_SSID = "Wokwi-GUEST";   // real hardware: your WiFi name
const char* WIFI_PASS = "";
const int WIFI_CHANNEL = 6;              // Wokwi-GUEST channel (speeds up connect)
const char* FW = "sitebox-1.0";

// ---- Pins (ESP32 DevKitC; 6-11 unused, 34-39 inputs only) ----
const int PIN_DHT = 15;
const int PIN_ONEWIRE = 4;        // DS18B20 DQ (4.7k pull-up to 3V3)
const int PIN_LDR = 34;           // LDR module AO (ADC1)
const int PIN_TANK_TRIG = 5;
const int PIN_TANK_ECHO = 18;
const int PIN_DRAIN_TRIG = 17;
const int PIN_DRAIN_ECHO = 16;
const int PIN_SDA = 21;           // OLED I2C
const int PIN_SCL = 22;
const int PIN_PIXELS = 13;        // NeoPixel ring DIN
const int PIN_BUZZER = 25;
const int PIN_SOS = 32;           // pushbutton to GND, INPUT_PULLUP
const int PIN_FAN_RELAY = 26;
const int PIN_PUMP_RELAY = 27;
const bool RELAY_ACTIVE_HIGH = true;     // most cheap real relay boards are active LOW

const int NUM_PIXELS = 12;
const unsigned long PERIOD_MS = 10000;   // telemetry every 10 s
const int MQTT_MAX_FAILS = 3;

// ---- Devices ----
DHTesp dht;
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature globe(&oneWire);
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
Adafruit_NeoPixel ring(NUM_PIXELS, PIN_PIXELS, NEO_GRB + NEO_KHZ800);
WiFiClientSecure mqttNet;
PubSubClient mqtt(mqttNet);

String topicTelemetry, topicCmd;
bool useMqtt = false;
int mqttFails = 0;
bool oledOk = false;

// ---- Last readings ----
float tempC = NAN, rh = NAN, globeC = NAN, tankCm = -1, drainCm = -1;
int lightRaw = 0;

// ---- State from the server ----
struct BoxState {
  bool valid = false;
  int levelIndex = 0;
  uint32_t color = 0x2FB344;
  String levelLabel = "";
  bool aaramNow = false, stopNow = false, fanOn = false, pumpOn = false, sosActive = false;
  String display[4];
} st;
String statusLine = "Booting";

// ---- SOS button ----
bool sosPending = false;         // pressed since the last report
bool sendNow = false;
int btnStable = HIGH, btnLast = HIGH;
unsigned long btnChangedAt = 0;

// ---- Buzzer pattern engine (non-blocking) ----
struct Note { uint16_t freq; uint16_t ms; };   // freq 0 = silence
const Note PATTERN_AARAM[] = {{2000, 250}, {0, 150}, {2000, 250}, {0, 150}, {2000, 250}, {0, 50}};
const Note PATTERN_STOP[] = {{1400, 400}, {2200, 400}, {1400, 400}, {2200, 400}, {1400, 400}, {2200, 400},
                             {1400, 400}, {2200, 400}, {0, 50}};
const Note PATTERN_SOS[] = {{3000, 80}, {0, 60}, {3000, 80}, {0, 50}};
const Note* buzPattern = nullptr;
int buzLen = 0, buzStep = 0;
unsigned long buzStepAt = 0;
bool prevAaram = false, prevStop = false;
unsigned long lastStopSirenAt = 0;
const unsigned long STOP_REPEAT_MS = 30000;

void playPattern(const Note* p, int len) {
  buzPattern = p; buzLen = len; buzStep = 0; buzStepAt = millis();
  if (p[0].freq) tone(PIN_BUZZER, p[0].freq); else noTone(PIN_BUZZER);
}

void buzzerTick() {
  if (!buzPattern) return;
  if (millis() - buzStepAt < buzPattern[buzStep].ms) return;
  buzStep++;
  if (buzStep >= buzLen) { noTone(PIN_BUZZER); buzPattern = nullptr; return; }
  buzStepAt = millis();
  if (buzPattern[buzStep].freq) tone(PIN_BUZZER, buzPattern[buzStep].freq); else noTone(PIN_BUZZER);
}

// ---- Relays ----
void setRelay(int pin, bool on) { digitalWrite(pin, (on == RELAY_ACTIVE_HIGH) ? HIGH : LOW); }

// ---- OLED ----
void splash(const String& status) {
  statusLine = status;
  Serial.println("[status] " + status);
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(2);
  oled.setCursor(34, 2);  oled.print("PEHRA");
  oled.setCursor(16, 22); oled.print("SITE BOX");
  oled.setTextSize(1);
  oled.drawLine(0, 42, 127, 42, SSD1306_WHITE);
  oled.setCursor(0, 50);  oled.print(status.substring(0, 21));
  oled.display();
}

void drawLevelBar(int y) {
  // 5 segments (kam .. khatarnak), filled up to level_index, label underneath.
  const int segW = 24, gap = 2, h = 10;
  for (int i = 0; i < 5; i++) {
    int x = i * (segW + gap);
    if (i <= st.levelIndex) oled.fillRect(x, y, segW, h, SSD1306_WHITE);
    else oled.drawRect(x, y, segW, h, SSD1306_WHITE);
  }
  oled.setCursor(0, y + 13);
  oled.print(st.levelLabel.substring(0, 14));
  oled.setCursor(92, y + 13);
  oled.print(useMqtt ? "MQTT" : "HTTP");
  if (st.sosActive && (millis() / 500) % 2) { oled.setCursor(122, y + 13); oled.print("!"); }
}

void drawScreen() {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextSize(1);
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextWrap(false);
  if (st.valid) {
    for (int i = 0; i < 4; i++) { oled.setCursor(0, i * 10); oled.print(st.display[i].substring(0, 21)); }
  } else {
    // No server state yet: show local readings so the box is still useful offline.
    char buf[32];
    snprintf(buf, sizeof buf, "Hawa %.1fC  RH %.0f%%", tempC, rh);              oled.setCursor(0, 0);  oled.print(buf);
    snprintf(buf, sizeof buf, "Globe %.1fC Dhoop %d", globeC, lightRaw * 100 / 4095); oled.setCursor(0, 10); oled.print(buf);
    snprintf(buf, sizeof buf, "Tank %.0f Naali %.0fcm", tankCm, drainCm);      oled.setCursor(0, 20); oled.print(buf);
    oled.setCursor(0, 30); oled.print(statusLine.substring(0, 21));
  }
  bool siren = st.valid && (st.aaramNow || st.stopNow);
  if (siren && (millis() / 1000) % 2 == 0) {
    // Big inverted banner: "AARAM ABHI" (10 chars x 12 px = 120 px at size 2)
    oled.fillRect(0, 42, 128, 22, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
    oled.setTextSize(2);
    oled.setCursor(4, 46);
    oled.print("AARAM ABHI");
    oled.setTextColor(SSD1306_WHITE);
    oled.setTextSize(1);
  } else {
    drawLevelBar(42);
  }
  oled.display();
}

// ---- NeoPixel: risk colour, breathing faster with level ----
void ringTick() {
  static unsigned long last = 0;
  if (millis() - last < 20) return;
  last = millis();
  uint32_t c = st.valid ? st.color : 0x2050FF;          // blue while waiting for the server
  int level = st.valid ? st.levelIndex : 0;
  const unsigned long periods[5] = {4000, 2500, 1500, 800, 400};
  unsigned long period = periods[constrain(level, 0, 4)];
  float phase = (float)(millis() % period) / period;
  float b = 0.15f + 0.85f * (0.5f - 0.5f * cosf(phase * 2 * PI));  // 15%..100%
  uint8_t r = ((c >> 16) & 0xFF) * b, g = ((c >> 8) & 0xFF) * b, bl = (c & 0xFF) * b;
  for (int i = 0; i < NUM_PIXELS; i++) ring.setPixelColor(i, ring.Color(r, g, bl));
  if (st.valid && st.sosActive && (millis() / 250) % 2) ring.setPixelColor(0, ring.Color(255, 255, 255));
  ring.show();
}

// ---- Sensors ----
float readDistanceCm(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  unsigned long us = pulseIn(echo, HIGH, 30000);
  return us == 0 ? -1 : us / 58.0;
}

void readSensors() {
  TempAndHumidity th = dht.getTempAndHumidity();
  tempC = th.temperature;
  rh = th.humidity;
  float g = globe.getTempCByIndex(0);                 // conversion was started last cycle
  globeC = (g == DEVICE_DISCONNECTED_C) ? NAN : g;
  globe.requestTemperatures();                        // async: ready by the next cycle
  // LDR module AO falls as light rises; invert so higher = brighter sun (contract).
  lightRaw = 4095 - analogRead(PIN_LDR);
  tankCm = readDistanceCm(PIN_TANK_TRIG, PIN_TANK_ECHO);
  delay(30);                                          // let the first echo die before the second ping
  drainCm = readDistanceCm(PIN_DRAIN_TRIG, PIN_DRAIN_ECHO);
}

String buildTelemetry(bool withToken) {
  JsonDocument doc;
  if (withToken) doc["token"] = DEVICE_TOKEN;
  if (!isnan(tempC)) doc["temp_c"] = round(tempC * 10) / 10.0;
  if (!isnan(rh)) doc["rh"] = round(rh);
  if (!isnan(globeC)) doc["globe_c"] = round(globeC * 10) / 10.0;
  doc["light_raw"] = lightRaw;
  if (tankCm > 0) doc["tank_distance_cm"] = round(tankCm * 10) / 10.0;
  if (drainCm > 0) doc["drain_distance_cm"] = round(drainCm * 10) / 10.0;
  doc["sos"] = sosPending;
  doc["fw"] = FW;
  String out;
  serializeJson(doc, out);
  return out;
}

// ---- Apply the server state (MQTT cmd or HTTPS response; same JSON) ----
uint32_t parseHexColor(const char* s) {
  if (!s) return 0x2FB344;
  if (*s == '#') s++;
  return (uint32_t)strtoul(s, nullptr, 16);
}

bool applyState(const char* json, size_t len) {
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, json, len);
  if (err) { Serial.printf("cmd: bad JSON (%s)\n", err.c_str()); return false; }
  if (doc["level_index"].isNull()) {
    const char* e = doc["error"] | (const char*)nullptr;
    if (!e) e = doc["message"] | "no level_index";
    Serial.printf("server: %s\n", e);
    statusLine = String("Server: ") + e;
    return false;
  }
  st.valid = true;
  st.levelIndex = constrain(doc["level_index"] | 0, 0, 4);
  st.color = parseHexColor(doc["color"] | "#2FB344");
  st.levelLabel = (const char*)(doc["level_label"] | "");
  st.aaramNow = doc["aaram_now"] | false;
  st.stopNow = doc["stop_now"] | false;
  st.fanOn = doc["fan_on"] | false;
  st.pumpOn = doc["pump_on"] | false;
  st.sosActive = doc["sos_active"] | false;
  JsonArrayConst lines = doc["display"].as<JsonArrayConst>();
  for (int i = 0; i < 4; i++) st.display[i] = (i < (int)lines.size()) ? String((const char*)(lines[i] | "")) : String("");

  setRelay(PIN_FAN_RELAY, st.fanOn);
  setRelay(PIN_PUMP_RELAY, st.pumpOn);

  // Siren: 3 beeps when aaram_now rises; continuous siren on stop_now, repeated every 30 s.
  if (st.stopNow && !prevStop) { playPattern(PATTERN_STOP, sizeof PATTERN_STOP / sizeof(Note)); lastStopSirenAt = millis(); }
  else if (st.aaramNow && !prevAaram) playPattern(PATTERN_AARAM, sizeof PATTERN_AARAM / sizeof(Note));
  prevAaram = st.aaramNow;
  prevStop = st.stopNow;

  Serial.printf("cmd: level=%d %s wbgt=%.1f aaram=%d stop=%d fan=%d pump=%d sos=%d\n", st.levelIndex,
                st.levelLabel.c_str(), (float)(doc["wbgt_c"] | 0.0), st.aaramNow, st.stopNow, st.fanOn,
                st.pumpOn, st.sosActive);
  for (int i = 0; i < 4; i++) if (st.display[i].length()) Serial.println("  | " + st.display[i]);
  return true;
}

// ---- MQTT (AWS IoT Core) ----
void onMqtt(char* topic, byte* payload, unsigned int len) {
  Serial.printf("MQTT message on %s (%u bytes)\n", topic, len);
  applyState((const char*)payload, len);
}

bool mqttConfigured() {
  return strlen(IOT_ENDPOINT) > 0 && strstr(DEVICE_CERT, "BEGIN CERTIFICATE") && strstr(DEVICE_KEY, "PRIVATE KEY");
}

bool mqttConnect() {
  if (mqtt.connected()) return true;
  splash("MQTT connecting...");
  Serial.printf("MQTT connecting to %s:8883 as %s\n", IOT_ENDPOINT, THING_NAME);
  if (mqtt.connect(THING_NAME)) {
    mqttFails = 0;
    mqtt.subscribe(topicCmd.c_str());
    Serial.println("MQTT connected, subscribed " + topicCmd);
    splash("MQTT connected");
    return true;
  }
  mqttFails++;
  Serial.printf("MQTT connect failed, state=%d (%d/%d)\n", mqtt.state(), mqttFails, MQTT_MAX_FAILS);
  if (mqttFails >= MQTT_MAX_FAILS) {
    useMqtt = false;
    Serial.println("MQTT gave up -> HTTPS fallback");
    splash("HTTPS fallback");
  }
  return false;
}

// ---- HTTPS fallback ----
void sendHttps(const String& body) {
  WiFiClientSecure client;
  client.setInsecure();   // fallback only: skips certificate check; MQTT path verifies Amazon Root CA 1
  HTTPClient http;
  String url = String(API_URL) + "/api/box";
  http.begin(client, url);
  http.setTimeout(10000);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  String reply = http.getString();
  http.end();
  Serial.printf("telemetry sent (HTTPS %d)\n", code);
  if (code <= 0) { statusLine = "HTTPS err " + String(code); return; }
  if (!applyState(reply.c_str(), reply.length())) Serial.println("  reply: " + reply.substring(0, 200));
}

void sendTelemetry() {
  readSensors();
  bool viaMqtt = useMqtt && mqttConnect();
  String body = buildTelemetry(!viaMqtt);
  Serial.println("telemetry: " + body);
  if (viaMqtt) {
    if (mqtt.publish(topicTelemetry.c_str(), body.c_str())) Serial.println("telemetry sent (MQTT " + topicTelemetry + ")");
    else Serial.println("MQTT publish failed");
  } else {
    sendHttps(body);
  }
  sosPending = false;
}

// ---- SOS button (debounced, falling edge) ----
void buttonTick() {
  int v = digitalRead(PIN_SOS);
  if (v != btnLast) { btnLast = v; btnChangedAt = millis(); }
  if (millis() - btnChangedAt > 40 && v != btnStable) {
    btnStable = v;
    if (v == LOW) {
      Serial.println("SOS pressed -> sending now");
      sosPending = true;
      sendNow = true;
      playPattern(PATTERN_SOS, sizeof PATTERN_SOS / sizeof(Note));
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\nPehra Site Box " + String(FW) + " thing=" + THING_NAME);

  pinMode(PIN_TANK_TRIG, OUTPUT);  pinMode(PIN_TANK_ECHO, INPUT);
  pinMode(PIN_DRAIN_TRIG, OUTPUT); pinMode(PIN_DRAIN_ECHO, INPUT);
  pinMode(PIN_SOS, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);  pinMode(PIN_PUMP_RELAY, OUTPUT);
  setRelay(PIN_FAN_RELAY, false);  setRelay(PIN_PUMP_RELAY, false);
  analogReadResolution(12);

  Wire.begin(PIN_SDA, PIN_SCL);
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (!oledOk) Serial.println("OLED not found at 0x3C");
  ring.begin();
  ring.setBrightness(120);
  ring.clear();
  ring.show();
  dht.setup(PIN_DHT, DHTesp::DHT22);
  globe.begin();
  globe.setWaitForConversion(false);
  globe.requestTemperatures();

  splash("WiFi connecting...");
  WiFi.begin(WIFI_SSID, WIFI_PASS, WIFI_CHANNEL);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(250); Serial.print("."); ringTick(); }
  Serial.println(" connected, IP " + WiFi.localIP().toString());
  splash("WiFi OK " + WiFi.localIP().toString());
  delay(800);

  topicTelemetry = String("pehra/box/") + THING_NAME + "/telemetry";
  topicCmd = String("pehra/box/") + THING_NAME + "/cmd";
  if (mqttConfigured()) {
    useMqtt = true;
    mqttNet.setCACert(AWS_ROOT_CA);
    mqttNet.setCertificate(DEVICE_CERT);
    mqttNet.setPrivateKey(DEVICE_KEY);
    mqtt.setServer(IOT_ENDPOINT, 8883);
    mqtt.setBufferSize(1024);
    mqtt.setKeepAlive(30);
    mqtt.setCallback(onMqtt);
    while (useMqtt && !mqttConnect()) delay(2000);
  } else {
    Serial.println("MQTT not configured (IOT_ENDPOINT/cert empty) -> HTTPS fallback");
    splash("HTTPS mode");
  }
  delay(600);       // DS18B20 first conversion
  sendNow = true;
}

void loop() {
  static unsigned long lastSend = 0;
  if (useMqtt) {
    if (!mqtt.connected()) {
      static unsigned long lastTry = 0;
      if (millis() - lastTry > 5000) { lastTry = millis(); mqttConnect(); }
    }
    mqtt.loop();
  }
  buttonTick();
  if (sendNow || millis() - lastSend >= PERIOD_MS) {
    sendNow = false;
    lastSend = millis();
    sendTelemetry();
  }
  if (st.valid && st.stopNow && !buzPattern && millis() - lastStopSirenAt >= STOP_REPEAT_MS) {
    lastStopSirenAt = millis();
    playPattern(PATTERN_STOP, sizeof PATTERN_STOP / sizeof(Note));
  }
  buzzerTick();
  ringTick();
  static unsigned long lastDraw = 0;
  if (millis() - lastDraw > 250) { lastDraw = millis(); drawScreen(); }
}
