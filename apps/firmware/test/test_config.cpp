#include <unity.h>

#include "config.h"

void test_audio_limits_monotonic() {
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 85.0f, sigma::config::kRecommendedMaxSplDb);
  TEST_ASSERT_TRUE(sigma::config::kRecommendedMaxSplDb <= sigma::config::kAbsoluteMaxSplDb);
}

void test_mic_bias_bounds() {
  TEST_ASSERT_TRUE(sigma::config::kMicBiasMinVolts >= 1.5f);
  TEST_ASSERT_TRUE(sigma::config::kMicBiasMaxVolts <= 3.6f);
  TEST_ASSERT_TRUE(sigma::config::kMicBiasMinVolts < sigma::config::kMicBiasMaxVolts);
}

void test_battery_thresholds() {
  TEST_ASSERT_TRUE(sigma::config::kBatteryCriticalVolts < sigma::config::kBatteryLowVolts);
  TEST_ASSERT_TRUE(sigma::config::kBatteryLowVolts <= sigma::config::kBatteryNominalVolts);
}

void setUp() {}
void tearDown() {}

int main(int, char**) {
  UNITY_BEGIN();
  RUN_TEST(test_audio_limits_monotonic);
  RUN_TEST(test_mic_bias_bounds);
  RUN_TEST(test_battery_thresholds);
  return UNITY_END();
}
