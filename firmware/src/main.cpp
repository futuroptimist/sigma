#include <Arduino.h>

#ifndef SIGMA_STATUS_LED
#define SIGMA_STATUS_LED 2
#endif

#ifndef SIGMA_BUTTON_PIN
#define SIGMA_BUTTON_PIN 0
#endif

#ifndef SIGMA_FIRMWARE_VERSION
#define SIGMA_FIRMWARE_VERSION "0.1.0"
#endif

namespace {
constexpr unsigned long kDebounceDelayMs = 10;
unsigned long last_sample_ms = 0;
bool button_state = false;
}

void setup() {
  pinMode(SIGMA_STATUS_LED, OUTPUT);
  pinMode(SIGMA_BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(SIGMA_STATUS_LED, LOW);
  Serial.begin(115200);
  Serial.println();
  Serial.print("Sigma firmware ready (v");
  Serial.print(SIGMA_FIRMWARE_VERSION);
  Serial.println(")");
  Serial.println("Press the button to toggle the status LED");
}

void loop() {
  const unsigned long now = millis();
  if (now - last_sample_ms < kDebounceDelayMs) {
    return;
  }

  last_sample_ms = now;
  const bool pressed = digitalRead(SIGMA_BUTTON_PIN) == LOW;
  if (pressed != button_state) {
    button_state = pressed;
    digitalWrite(SIGMA_STATUS_LED, pressed ? HIGH : LOW);
    Serial.print("Button state: ");
    Serial.println(pressed ? "pressed" : "released");
  }
}
