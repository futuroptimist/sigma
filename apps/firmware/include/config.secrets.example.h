#pragma once

// Populate this file with private credentials required by optional integrations
// (e.g. Wi-Fi SSIDs, API keys).  Copy to `config.secrets.h` and keep the real
// file excluded from version control.

namespace sigma::secrets {
constexpr const char* kWifiSsid = "YOUR_WIFI_SSID";
constexpr const char* kWifiPassword = "YOUR_WIFI_PASSWORD";  // pragma: allowlist secret
constexpr const char* kApiKey = "TOKEN_PLACEHOLDER";  // pragma: allowlist secret
}  // namespace sigma::secrets
