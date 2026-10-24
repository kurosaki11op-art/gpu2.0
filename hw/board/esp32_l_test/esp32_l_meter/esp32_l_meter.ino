// ESP32 L test for a MULTIMETER: speed and logic on the board, current read by you. No sensor, no extra parts.
// Wiring: 5V source (charger / power bank, cut USB cable) red wire -> multimeter (mA range, red probe in the mA socket) -> ESP32 VIN pin; source GND -> ESP32 GND.
//   Start on the 200 mA range. The meter sits in series with the 5V wire.
// Phases (LED = GPIO2, the board's blue LED): IDLE = LED off for 30 s, RUN = LED on for 30 s, 5 repetitions; each repetition starts with 3 quick blinks.
//   Write down the stable reading at the END of each phase (about 25 s in): idle_mA, run_mA.
// No USB during the run. At boot wait 8 s for 's' on USB serial: if received, print the stored results (speed per repetition) and stop.
#include <Preferences.h>
#include "l_decide.h"
#define PHASE_S 30
#define REPS 5
Preferences pref; String logbuf;
static void emit(const String &l) { Serial.print(l); logbuf += l; pref.putString("log", logbuf); }
void setup() {
  Serial.begin(115200); pref.begin("lmeter", false); pinMode(2, OUTPUT); digitalWrite(2, LOW);
  uint32_t tw = millis(); while (millis() - tw < 8000) { if (Serial.available() && Serial.read() == 's') { Serial.println(pref.getString("log", "(nothing stored)")); for (;;) delay(1000); } delay(10); }
  pref.putString("log", ""); logbuf = "";
  int bad = 0; for (int i = 0; i < L_NIMG; i++) if (l_decide(i, 0) != L_EXPECT[i]) bad++;
  { char b[96]; snprintf(b, sizeof b, "LOGIC %s %d of %d\n", bad ? "FAIL" : "PASS", bad, L_NIMG); emit(b); }
  volatile int sink = 0;
  for (int r = 0; r < REPS; r++) {
    for (int k = 0; k < 3; k++) { digitalWrite(2, HIGH); delay(120); digitalWrite(2, LOW); delay(120); }
    digitalWrite(2, LOW); delay(PHASE_S * 1000);                                     // IDLE: LED off
    digitalWrite(2, HIGH); uint32_t t0 = micros(), n = 0;                            // RUN: LED on
    while (micros() - t0 < PHASE_S * 1000000UL) { for (int i = 0; i < L_NIMG; i++) sink += l_decide(i, 0); n += L_NIMG; }
    uint32_t dt = micros() - t0; digitalWrite(2, LOW);
    char rb[160]; snprintf(rb, sizeof rb, "REP %d decisions %lu run_s %.3f us_per_decision %.2f\n", r, (unsigned long)n, dt / 1e6, (float)dt / n); emit(rb);
  }
  { char db[48]; snprintf(db, sizeof db, "DONE cpu_mhz %d\n", getCpuFrequencyMhz()); emit(db); }
}
void loop() { digitalWrite(2, !digitalRead(2)); delay(100); }
