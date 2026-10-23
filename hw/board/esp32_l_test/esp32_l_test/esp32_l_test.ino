// L logic + speed test on an ESP32 (Arduino core). Open this folder's sketch as esp32_l_test (the .ino must sit in a folder of the same name).
// 1. Logic test: 200 clothing images, prediction must equal the Python model's for every image (prints PASS/FAIL).
// 2. Speed: microseconds per decision (about 570 active bits x 10 classes, byte adds only).
// 3. Power: GPIO4 is HIGH while the decision loop runs, so the existing INA219 logger (../esp32_ina219_logger, trigger on GPIO4 of a
//    SECOND ESP32, or read the same board's INA219 directly) can integrate energy over the loop. Repeat loop count REPS so the loop lasts seconds.
// Table: 4608 x 10 bytes = 46 KB in flash (const), no RAM needed.
#include "l_decide.h"
#define TRIG 4
#define REPS 200
void setup() {
  Serial.begin(115200); pinMode(TRIG, OUTPUT); digitalWrite(TRIG, LOW); delay(1500);
  int bad = 0; for (int i = 0; i < L_NIMG; i++) if (l_decide(i, 0) != L_EXPECT[i]) bad++;
  Serial.printf("LOGIC %s (%d of %d differ)\n", bad ? "FAIL" : "PASS", bad, L_NIMG);
}
void loop() {
  volatile int sink = 0; delay(2000);
  digitalWrite(TRIG, HIGH); uint32_t t0 = micros();
  for (int r = 0; r < REPS; r++) for (int i = 0; i < L_NIMG; i++) sink += l_decide(i, 0);
  uint32_t dt = micros() - t0; digitalWrite(TRIG, LOW);
  Serial.printf("RUN %d decisions in %lu us = %.1f us each (cpu %d MHz)\n", REPS * L_NIMG, (unsigned long)dt, (float)dt / (REPS * L_NIMG), getCpuFrequencyMhz());
}
