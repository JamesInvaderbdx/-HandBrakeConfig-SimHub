// Frein à main DIY — Potentiomètre B103 sur A0
// Compatible HandBrakeConfig SimHub Plugin (eKLID)

#define PIN_POT  A0
#define INVERT   false
#define SAMPLES  8

static uint16_t buf[SAMPLES];
static uint8_t  idx = 0;

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < SAMPLES; i++) buf[i] = analogRead(PIN_POT);
}

void loop() {
  buf[idx] = analogRead(PIN_POT);
  idx = (idx + 1) % SAMPLES;
  uint32_t sum = 0;
  for (uint8_t i = 0; i < SAMPLES; i++) sum += buf[i];
  uint16_t val = sum / SAMPLES;
  Serial.println(INVERT ? 1023 - val : val);
  delay(10);
}
