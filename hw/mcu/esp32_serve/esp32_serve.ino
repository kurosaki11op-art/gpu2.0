// L chip algorithm on an ESP32 as an image server over USB serial (31 Oct 2026). The host (hw/mcu/serve_host.py) sends one 28 x 28 image at a time; the ESP32 classifies it with the L algorithm and replies with the class, the routed and flag bits,
// the margin of the final scores and the time the classification took. This lets the whole 10,000-image test set run on the real ESP32 (a MEASURED accuracy and a bit-exactness check at scale) and lets the host act as the fallback for the flagged images (the chip-first cascade on hardware).
// Board: "ESP32 Dev Module". Keep the four files of this folder together: esp32_serve.ino, l_core.c, l_core.h, l_tables.h. Close the Serial Monitor before running the host script (only one program can hold the port).
// Protocol (binary, after the text banner "L-SERVE READY" printed at start and on ping):
//   host -> board  0xA5 + 784 bytes        classify an image; reply 11 bytes: 0x5A, class, status (bit 0 = routed to L Deep, bit 1 = flagged), margin (int32 little endian), microseconds spent in the classification (uint32 little endian)
//   host -> board  0xA6 + 3 bytes          set the reject threshold (20 bits, least significant byte first); reply 0x5C
//   host -> board  0xA8                    ping; the board prints the banner line again
#include <WiFi.h>
extern "C" {
#include "l_core.h"
}
#define BAUD 921600           // if the transfer is unreliable (a cheap USB-serial chip) change to 460800 or 115200 here and use --baud in the host script
static uint8_t img[784];
static int32_t reject_t = 3304;   // the host sets it before a run
void setup() {
  Serial.setRxBufferSize(2048);
  Serial.begin(BAUD);
  setCpuFrequencyMhz(240);
  WiFi.mode(WIFI_OFF);
  btStop();
  Serial.println("L-SERVE READY");
}
void loop() {
  if (!Serial.available()) return;
  int b = Serial.read();
  if (b == 0xA5) {
    Serial.setTimeout(1000);
    if (Serial.readBytes(img, 784) != 784) { while (Serial.available()) Serial.read(); Serial.write((uint8_t)0xEE); return; }
    l_result r;
    uint32_t t0 = micros();
    l_classify(img, reject_t, &r);
    uint32_t dt = micros() - t0;
    uint8_t out[11];
    out[0] = 0x5A; out[1] = (uint8_t)r.pred; out[2] = (uint8_t)((r.routed ? 1 : 0) | (r.flag ? 2 : 0));
    memcpy(out + 3, &r.margin, 4);
    memcpy(out + 7, &dt, 4);
    Serial.write(out, 11);
  } else if (b == 0xA6) {
    uint8_t t[3];
    Serial.setTimeout(1000);
    if (Serial.readBytes(t, 3) != 3) { Serial.write((uint8_t)0xEE); return; }
    reject_t = (int32_t)(t[0] | (t[1] << 8) | ((t[2] & 15) << 16));
    Serial.write((uint8_t)0x5C);
  } else if (b == 0xA8) {
    Serial.println("L-SERVE READY");
  }
}
