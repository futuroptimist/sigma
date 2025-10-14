#pragma once

#include <stdint.h>

/**
 * @file config.h
 * Centralized device configuration for the Sigma firmware.
 *
 * Update this file to tune hardware mappings and firmware safety rails.  Do not
 * commit credentials here—place them in `config.secrets.h` (see the provided
 * example file) and keep the real file out of source control.
 */

namespace sigma::config {

// Firmware metadata ---------------------------------------------------------

constexpr const char* kFirmwareVersion = "0.1.0";
constexpr uint32_t kSerialBaudRate = 115200;

// Hardware mappings ---------------------------------------------------------

constexpr uint8_t kStatusLedPin = 2;
constexpr uint8_t kButtonPin = 0;

// Audio safety rails --------------------------------------------------------
// All SPL values are referenced to 20 µPa (dB SPL).  Stay below 85 dB for
// prolonged use; firmware asserts if configuration exceeds hard limits.
constexpr float kRecommendedMaxSplDb = 85.0f;
constexpr float kAbsoluteMaxSplDb = 94.0f;

// Microphone bias limits – keep between 1.8 V and 3.3 V to avoid damage.
constexpr float kMicBiasMinVolts = 1.8f;
constexpr float kMicBiasMaxVolts = 3.3f;

// Battery protection thresholds --------------------------------------------
constexpr float kBatteryNominalVolts = 3.7f;
constexpr float kBatteryLowVolts = 3.3f;
constexpr float kBatteryCriticalVolts = 3.0f;

}  // namespace sigma::config

#ifdef SIGMA_INCLUDE_SECRETS
#include "config.secrets.h"
#endif
