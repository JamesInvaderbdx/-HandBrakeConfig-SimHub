// Joystick KY-023 – Arduino Nano
// X → A1 | Y → A2 | SW → D2

#define PIN_X  A1
#define PIN_Y  A2
#define PIN_SW 2

void setup() {
  Serial.begin(9600);
  pinMode(PIN_SW, INPUT_PULLUP);
}

void loop() {
  int x   = analogRead(PIN_X);    // 0–1023
int y = analogRead(PIN_Y);  // 0–1023
  bool sw = !digitalRead(PIN_SW); // true = pressé

  Serial.print("X:"); Serial.print(x);
  Serial.print(" Y:"); Serial.print(y);
  Serial.print(" SW:"); Serial.println(sw);

  delay(100);
}
