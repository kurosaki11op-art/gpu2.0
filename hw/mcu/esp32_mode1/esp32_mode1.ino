// Small reference CNN (int8) on an ESP32, MODE 1 only (31 Oct 2026). A REFERENCE BASELINE for the energy measurement, not a part of L. Runs the CNN over the same 40 embedded Fashion-MNIST test images as esp32_mode0 in an endless loop
// and prints time per image, a checksum and the accuracy on the embedded images after every pass. Use the USB power meter in the supply line while it runs (see hw/mcu/README.md).
// Board: "ESP32 Dev Module". Keep the five files of this folder together: esp32_mode1.ino, cnn_core.c, cnn_core.h, cnn_tables.h, l_testimg.h. The CNN is slow on an ESP32: one report line takes tens of seconds.
#include <WiFi.h>
extern "C" {
#include "cnn_core.h"
}
#include "l_testimg.h"
#define PASSES 1        // passes over the 40 embedded images per report line
const int MARK_PIN = 2; // on-board LED pin on most ESP32 dev boards: high while inferences run
void setup() {
  Serial.begin(115200);
  setCpuFrequencyMhz(240);
  WiFi.mode(WIFI_OFF);
  btStop();
  pinMode(MARK_PIN, OUTPUT);
  Serial.printf("Small CNN (int8), MODE 1, CPU %d MHz, WiFi and Bluetooth off, code version 3 (O3)\n", getCpuFrequencyMhz());
}
void loop() {
  uint32_t checksum = 0;
  int correct = 0;
  digitalWrite(MARK_PIN, HIGH);
  uint32_t t0 = micros();
  for (int p = 0; p < PASSES; p++) {
    for (int i = 0; i < L_NTEST; i++) {
      int c = cnn_classify(&L_TEST_IMG[784 * i], NULL);
      checksum += c;
      correct += (c == L_TEST_LABEL[i]);
    }
  }
  uint32_t dt = micros() - t0;
  digitalWrite(MARK_PIN, LOW);
  int n = PASSES * L_NTEST;
  Serial.printf("%d images in %lu us = %.3f ms per image, %.2f images per second; checksum %lu; accuracy on the embedded images %.1f%%\n",
                n, (unsigned long)dt, dt / 1000.0 / n, n * 1e6 / dt, (unsigned long)checksum, 100.0 * correct / n);
  delay(50);
}
