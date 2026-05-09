// Frein à main DIY — Potentiomètre B103 sur A1
// Compatible HandBrakeConfig SimHub Plugin (eKLID)

#define PIN_POT A0

void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(PIN_POT));
  delay(10);
}
