// Pehra Site Box: per-device secrets for real hardware (Arduino IDE / PlatformIO).
// Copy to secrets.h (never commit it), fill in, then replace the "// ==== CONFIG ====" block at the top of
// sketch.ino with:  #include "secrets.h"
// In Wokwi the same values live inline between the CONFIG markers (Wokwi web projects take extra files badly).
// The names must stay exactly as below; the provisioning script fills the same names.
#pragma once

const char* THING_NAME = "PASTE_THING_NAME";                 // AWS IoT thing name (= box id = MQTT client id)
const char* IOT_ENDPOINT = "";                               // "xxxxxxxx-ats.iot.ap-south-1.amazonaws.com"; empty = HTTPS only
const char* API_URL = "https://yj61i9i7g0.execute-api.ap-south-1.amazonaws.com";
const char* DEVICE_TOKEN = "PASTE_DEVICE_TOKEN";             // "dev_..." for the HTTPS fallback

// Amazon Root CA 1 (public): https://www.amazontrust.com/repository/AmazonRootCA1.pem
const char AWS_ROOT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
PASTE_AMAZON_ROOT_CA_1_HERE (sketch.ino already contains the real one)
-----END CERTIFICATE-----
)EOF";

// Device certificate from AWS IoT (xxxx-certificate.pem.crt)
const char DEVICE_CERT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
PASTE_DEVICE_CERTIFICATE_HERE
-----END CERTIFICATE-----
)EOF";

// Device private key from AWS IoT (xxxx-private.pem.key). Secret: one per box, never shared.
const char DEVICE_KEY[] PROGMEM = R"EOF(
-----BEGIN RSA PRIVATE KEY-----
PASTE_DEVICE_PRIVATE_KEY_HERE
-----END RSA PRIVATE KEY-----
)EOF";
