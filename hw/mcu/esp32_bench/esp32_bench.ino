// ESP32 energy benchmark (30 Oct 2026): runs the L chip algorithm (MODE 0), the small reference CNN (MODE 1) or an idle baseline (MODE 2) in an endless loop over 40 embedded Fashion-MNIST test images, while a USB power meter in the supply line records the average power.
// NOT YET RUN ON AN ESP32: the C cores are verified bit-exact on a PC (hw/mcu/main_pc.c, main_pc_cnn.c); this sketch only wraps them. See hw/mcu/README.md for the measurement procedure.
// Arduino IDE or PlatformIO, board "ESP32 Dev Module". The two cores are included as source from the parent folder (one translation unit).
#define MODE 0                // 0 = L algorithm, 1 = small CNN (int8), 2 = idle baseline (the CPU awake, no inference)
#define REJECT_T 3304         // reject threshold of the L chip (MODE 0): flagged answers would go to a fallback; 3304 flags about 20% of the images
#if MODE == 1
#define PASSES 1              // the CNN is slow on an ESP32: one pass over the 40 embedded images per report line
#else
#define PASSES 25             // passes over the 40 embedded images per report line (40 x 25 = 1,000 images)
#endif
#include <WiFi.h>
extern "C" {
#include "../l_core.h"
#include "../cnn_core.h"
}
#include "../l_core.c"
#include "../cnn_core.c"
#include "../l_testimg.h"
const int MARK_PIN = 2;       // the on-board LED pin: high while inferences run, low during the report (a scope or logic analyser can time the loop on it)
void setup() {
  Serial.begin(115200); setCpuFrequencyMhz(240); WiFi.mode(WIFI_OFF); btStop(); pinMode(MARK_PIN, OUTPUT);
  Serial.printf("L energy benchmark: MODE %d, CPU %d MHz, WiFi and Bluetooth off\n", MODE, getCpuFrequencyMhz());
}
void loop() {
  uint32_t checksum = 0; int agree = 0, correct = 0, flagged = 0, routed = 0; digitalWrite(MARK_PIN, HIGH); uint32_t t0 = micros();
  for (int p = 0; p < PASSES; p++) {
    for (int i = 0; i < L_NTEST; i++) {
#if MODE == 0
      l_result r; l_classify(&L_TEST_IMG[784 * i], REJECT_T, &r); checksum += r.pred; agree += (r.pred == L_TEST_PRED[i]); correct += (r.pred == L_TEST_LABEL[i]); flagged += r.flag; routed += r.routed;
#elif MODE == 1
      int c = cnn_classify(&L_TEST_IMG[784 * i], NULL); checksum += c; correct += (c == L_TEST_LABEL[i]);
#else
      delay(10);                                   // idle: the FreeRTOS idle task runs, the CPU is not busy
#endif
    }
  }
  uint32_t dt = micros() - t0; digitalWrite(MARK_PIN, LOW); int n = PASSES * L_NTEST;
  Serial.printf("MODE %d: %d images in %lu us = %.3f ms per image, %.1f images per second; checksum %lu; accuracy on the embedded images %.1f%%", MODE, n, (unsigned long)dt, dt / 1000.0 / n, n * 1e6 / dt, (unsigned long)checksum, 100.0 * correct / n);
#if MODE == 0
  Serial.printf("; identical to the model on %d of %d; routed %d, flagged %d", agree, n, routed, flagged);
#endif
  Serial.println(); delay(50);
}
