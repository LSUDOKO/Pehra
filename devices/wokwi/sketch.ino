// Invisible Heat site sensor - ESP32 + DHT22 (temperature, humidity) + HC-SR04 (water level).
// Runs on real hardware or free in the Wokwi simulator (wokwi.com), whose virtual WiFi
// "Wokwi-GUEST" reaches the internet. Readings go to the deployed Invisible Heat API, which turns
// them into a site-corrected WBGT, tank-level and drain-level alerts. The red LED and buzzer
// follow the server's "alert" answer.
//
// Setup: in Telegram/WhatsApp send "/device weather" and "/device tank 120" (or "drain 100"),
// paste the two tokens below, then press Play. Move the DHT22 / HC-SR04 sliders to test.

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "DHTesp.h"

const char* WIFI_SSID = "Wokwi-GUEST";   // real hardware: your WiFi name
const char* WIFI_PASS = "";
const char* API_URL = "https://yj61i9i7g0.execute-api.ap-south-1.amazonaws.com/api/sensor";
const char* WEATHER_TOKEN = "PASTE_WEATHER_TOKEN";   // from "/device weather"
const char* LEVEL_TOKEN = "PASTE_TANK_OR_DRAIN_TOKEN"; // from "/device tank 120" or "/device drain 100"

const int DHT_PIN = 15;
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN = 2;
const int BUZZER_PIN = 4;
const unsigned long PERIOD_MS = 15000;    // the API accepts up to 12 readings a minute per device

DHTesp dht;
bool weatherAlert = false, levelAlert = false;

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long us = pulseIn(ECHO_PIN, HIGH, 30000);
  return us == 0 ? -1 : us / 58.0;
}

// POST one JSON body; returns true if the server says this reading is an alert.
bool postReading(const String& body) {
  WiFiClientSecure client;
  client.setInsecure();   // demo: skip certificate pinning; pin the API certificate in production
  HTTPClient http;
  http.begin(client, API_URL);
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(body);
  String reply = http.getString();
  http.end();
  Serial.printf("POST %d -> %s\n", code, reply.c_str());
  return code == 200 && reply.indexOf("\"alert\": true") >= 0;
}

void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  dht.setup(DHT_PIN, DHTesp::DHT22);
  WiFi.begin(WIFI_SSID, WIFI_PASS, 6);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(250); Serial.print("."); }
  Serial.println(" connected");
}

void loop() {
  TempAndHumidity th = dht.getTempAndHumidity();
  if (!isnan(th.temperature) && !isnan(th.humidity) && String(WEATHER_TOKEN).startsWith("dev_")) {
    String body = String("{\"device_token\":\"") + WEATHER_TOKEN + "\",\"temp_c\":" + String(th.temperature, 1) +
                  ",\"rh\":" + String(th.humidity, 0) + "}";
    weatherAlert = postReading(body);
  }
  float cm = readDistanceCm();
  if (cm > 0 && String(LEVEL_TOKEN).startsWith("dev_")) {
    String body = String("{\"device_token\":\"") + LEVEL_TOKEN + "\",\"distance_cm\":" + String(cm, 1) + "}";
    levelAlert = postReading(body);
  }
  bool alert = weatherAlert || levelAlert;
  digitalWrite(LED_PIN, alert ? HIGH : LOW);
  if (alert) { tone(BUZZER_PIN, 2000, 400); }
  delay(PERIOD_MS);
}
