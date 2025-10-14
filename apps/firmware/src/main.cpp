#include <Arduino.h>

#include "config.h"

namespace {
constexpr unsigned long kDebounceDelayMs = 10;
unsigned long last_sample_ms = 0;
bool button_state = false;

void enforce_audio_safety() {
  if (sigma::config::kRecommendedMaxSplDb > sigma::config::kAbsoluteMaxSplDb) {
    Serial.println("[safety] Recommended SPL exceeds absolute maximum – check config.h");
  }
}

void report_safety_callouts() {
  Serial.print("[safety] Maintain SPL under ");
  Serial.print(sigma::config::kRecommendedMaxSplDb);
  Serial.println(" dB for extended sessions (absolute max 94 dB).");
  Serial.print("[safety] Keep mic bias between ");
  Serial.print(sigma::config::kMicBiasMinVolts);
  Serial.print(" V and ");
  Serial.print(sigma::config::kMicBiasMaxVolts);
  Serial.println(" V.");
  Serial.print("[safety] Stop use if battery drops below ");
  Serial.print(sigma::config::kBatteryLowVolts);
  Serial.println(" V (critical at 3.0 V).");
}
}  // namespace

void setup() {
  pinMode(sigma::config::kStatusLedPin, OUTPUT);
  pinMode(sigma::config::kButtonPin, INPUT_PULLUP);
  digitalWrite(sigma::config::kStatusLedPin, LOW);
  Serial.begin(sigma::config::kSerialBaudRate);
  Serial.println();
  Serial.print("Sigma firmware ready (v");
  Serial.print(sigma::config::kFirmwareVersion);
  Serial.println(")");
  Serial.println("Press the button to toggle the status LED");
  enforce_audio_safety();
  report_safety_callouts();
}

void loop() {
  const unsigned long now = millis();
  if (now - last_sample_ms < kDebounceDelayMs) {
    return;
  }

  last_sample_ms = now;
  const bool pressed = digitalRead(sigma::config::kButtonPin) == LOW;
  if (pressed != button_state) {
    button_state = pressed;
    digitalWrite(sigma::config::kStatusLedPin, pressed ? HIGH : LOW);
    Serial.print("Button state: ");
    Serial.println(pressed ? "pressed" : "released");
  }
}
