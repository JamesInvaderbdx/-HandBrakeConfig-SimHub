// HandBrake DIY — KY-023
// Compatible HandBrakeConfig SimHub Plugin (eKLID)
// VRx → A0   VRy → A1  — changer PIN_BRAKE selon l'axe qui répond

#include <Arduino.h>
#define PIN_BRAKE A0   // A0 = axe X, A1 = axe Y — tester les deux
#define INVERT    true  // true = inverse le sens si nécessaire
#define SAMPLES   8

static uint16_t buf[SAMPLES];
static uint8_t  idx = 0;

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < SAMPLES; i++) buf[i] = analogRead(PIN_BRAKE);
}

void loop() {
  buf[idx] = analogRead(PIN_BRAKE);
  idx = (idx + 1) % SAMPLES;
  uint32_t sum = 0;
  for (uint8_t i = 0; i < SAMPLES; i++) sum += buf[i];
  uint16_t val = sum / SAMPLES;
  Serial.println(INVERT ? 1023 - val : val);
  delay(10);
}
