// HandBrake DIY — KY-023
// Compatible HandBrakeConfig SimHub Plugin (eKLID)
// VRx → A1   VRy → A0  — changer PIN_BRAKE selon l'axe qui répond

#include <Arduino.h>

// --- CONFIG ---
// MODE_TEST true  : affiche A0 et A1 en parallèle pour identifier l'axe du frein
// MODE_TEST false : mode normal, seul PIN_BRAKE est envoyé au plugin
#define MODE_TEST  false

#define PIN_BRAKE  A1    // A1=VRx — axe confirmé pour le frein à main
#define INVERT     true  // true = inverse le sens si nécessaire
#define SAMPLES    8

static uint16_t bufA0[SAMPLES];
static uint16_t bufA1[SAMPLES];
static uint8_t  idx = 0;

static uint16_t average(uint16_t* buf) {
  uint32_t sum = 0;
  for (uint8_t i = 0; i < SAMPLES; i++) sum += buf[i];
  return sum / SAMPLES;
}

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < SAMPLES; i++) {
    bufA0[i] = analogRead(A0);
    bufA1[i] = analogRead(A1);
  }
}

void loop() {
  bufA0[idx] = analogRead(A0);
  bufA1[idx] = analogRead(A1);
  idx = (idx + 1) % SAMPLES;

#if MODE_TEST
  // Tirer le frein et observer lequel des deux valeurs bouge
  Serial.print("A0(VRy)=");
  Serial.print(average(bufA0));
  Serial.print("  A1(VRx)=");
  Serial.println(average(bufA1));
#else
  uint16_t val = (PIN_BRAKE == A0) ? average(bufA0) : average(bufA1);
  Serial.println(INVERT ? 1023 - val : val);
#endif

  delay(10);
}
