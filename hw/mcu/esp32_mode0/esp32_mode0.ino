// L chip algorithm on an ESP32, MODE 0 only (31 Oct 2026). Runs the integer pipeline of the L chip (encoder, counting table, dispatcher, L Deep clauses, reject flag) over 40 embedded Fashion-MNIST test images in an endless loop,
// and prints time per image, a checksum and agreement with the model after every 1,000 images. Use a USB power meter in the supply line to measure power while it runs (see hw/mcu/README.md).
// Board: "ESP32 Dev Module" (Arduino IDE or PlatformIO). Keep the five files of this folder together: esp32_mode0.ino, l_core.c, l_core.h, l_tables.h, l_testimg.h.
#include <WiFi.h>
extern "C" {
#include "l_core.h"
}
#include "l_testimg.h"
#define REJECT_T 3304   // reject threshold: answers whose final margin is at or below it are flagged for a fallback (3304 flags about 20% of the images)
#define PASSES 25       // passes over the 40 embedded images per report line (40 x 25 = 1,000 images)
const int MARK_PIN = 2; // the on-board LED pin on most ESP32 dev boards: high while inferences run, low during the report
static uint32_t clk_us() { return micros(); }
void setup() {
  Serial.begin(115200);
  setCpuFrequencyMhz(240);
  WiFi.mode(WIFI_OFF);
  btStop();
  pinMode(MARK_PIN, OUTPUT);
  l_clock = clk_us;   // per-stage timing (adds a few microseconds per image)
  Serial.printf("L algorithm, MODE 0, CPU %d MHz, WiFi and Bluetooth off, code version 2 (shift-add popcount, per-stage timing)\n", getCpuFrequencyMhz());
}
void loop() {
  uint32_t checksum = 0;
  int agree = 0, correct = 0, flagged = 0, routed = 0;
  l_prof[0] = l_prof[1] = l_prof[2] = l_prof[3] = 0;
  digitalWrite(MARK_PIN, HIGH);
  uint32_t t0 = micros();
  for (int p = 0; p < PASSES; p++) {
    for (int i = 0; i < L_NTEST; i++) {
      l_result r;
      l_classify(&L_TEST_IMG[784 * i], REJECT_T, &r);
      checksum += r.pred;
      agree += (r.pred == L_TEST_PRED[i]);
      correct += (r.pred == L_TEST_LABEL[i]);
      flagged += r.flag;
      routed += r.routed;
    }
  }
  uint32_t dt = micros() - t0;
  digitalWrite(MARK_PIN, LOW);
  int n = PASSES * L_NTEST;
  Serial.printf("%d images in %lu us = %.3f ms per image, %.1f images per second; checksum %lu; identical to the model on %d of %d; accuracy on the embedded images %.1f%%; routed %d, flagged %d\n",
                n, (unsigned long)dt, dt / 1000.0 / n, n * 1e6 / dt, (unsigned long)checksum, agree, n, 100.0 * correct / n, routed, flagged);
  Serial.printf("  per image: receptors %.3f ms, detectors %.3f ms, stage 1 %.3f ms, stage 2 %.3f ms (averaged over all images; stage 2 runs on the %d routed ones)\n",
                l_prof[0] / 1000.0 / n, l_prof[1] / 1000.0 / n, l_prof[2] / 1000.0 / n, l_prof[3] / 1000.0 / n, routed);
  delay(50);
}
