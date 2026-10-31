// Idle baseline on an ESP32, MODE 2 only (31 Oct 2026): the processor is awake at 240 MHz with Wi-Fi and Bluetooth off, but runs no inference (the FreeRTOS idle task runs between short delays).
// The USB power meter reading in this mode is P_idle; energy per image of the other two modes is (P_mode - P_idle) x time per image. See hw/mcu/README.md. Only this one file is needed.
#include <WiFi.h>
const int MARK_PIN = 2; // on-board LED pin on most ESP32 dev boards: kept LOW here, so the LED does not change the reading
void setup() {
  Serial.begin(115200);
  setCpuFrequencyMhz(240);
  WiFi.mode(WIFI_OFF);
  btStop();
  pinMode(MARK_PIN, OUTPUT);
  digitalWrite(MARK_PIN, LOW);
  Serial.printf("Idle baseline, MODE 2, CPU %d MHz, WiFi and Bluetooth off\n", getCpuFrequencyMhz());
}
void loop() {
  delay(1000);
  Serial.println("idle");
}
