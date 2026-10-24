// ESP32 self-measuring test of the L decision: logic + speed + power on ONE board with ONE INA219.
// Wiring: USB 5V -> INA219 VIN+ ; INA219 VIN- -> ESP32 VIN/5V pin ; GNDs common ; INA219 VCC -> ESP32 3V3, SDA -> GPIO21, SCL -> GPIO22.
//   (the INA219's own ~1 mA is drawn through the ESP32 regulator, i.e. inside the measurement, and cancels in the idle-vs-run difference)
// Library: "Adafruit INA219". Board: ESP32 Dev Module (dual core). Serial monitor / logger at 115200.
// Method: core 0 runs a sampler task that reads the INA219 continuously (same in every phase, so its own load cancels);
//         core 1 runs the L decisions in the RUN phase and sleeps in the IDLE phase. Wi-Fi and Bluetooth are never started.
//         REPS repetitions of IDLE (PHASE_S s) then RUN (PHASE_S s). Delta power = P_run - P_idle; energy per decision = delta power / rate.
// NO SERIAL ADAPTER NEEDED: at boot the sketch waits 8 s for the character 's' on USB serial. If it gets 's' it prints the results of the last run (saved in flash) and stops.
//   If not, it runs the measurement (no USB needed, power the board only through the INA219) and saves the lines to flash; the board then blinks the LED (GPIO2) when done.
//   Procedure: 1) flash with USB. 2) unplug USB, power through the INA219 path, wait for the LED to blink (about 80 s). 3) power off, plug USB, open the monitor at 115200, press EN and send 's' within 8 s.
// Output lines (all start with a keyword, the PC script check_esp32_run.py parses them):
//   LOGIC PASS|FAIL <n differ> of <N>
//   REP <i> idle_mA <x> run_mA <y> bus_V <v> decisions <n> run_s <t> us_per_decision <u> samples_idle <a> samples_run <b>
//   DONE cpu_mhz <f>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <Preferences.h>
#include "l_decide.h"
#define PHASE_S 6
#define REPS 5
Adafruit_INA219 ina;
volatile int phase = 0;                 // 0 idle, 1 run, 2 stop sampling
volatile double sum_ma[2] = {0, 0}, sum_v[2] = {0, 0}; volatile uint32_t ns[2] = {0, 0};
static void sampler(void *) {
  for (;;) {
    int p = phase;
    if (p < 2) { float ma = ina.getCurrent_mA(), v = ina.getBusVoltage_V(); sum_ma[p] += ma; sum_v[p] += v; ns[p]++; }
    vTaskDelay(1);
  }
}
Preferences pref; String logbuf;
static void emit(const String &l) { Serial.print(l); logbuf += l; pref.putString("log", logbuf); }
void setup() {
  Serial.begin(115200); pref.begin("ltest", false); pinMode(2, OUTPUT);
  uint32_t tw = millis(); while (millis() - tw < 8000) { if (Serial.available() && Serial.read() == 's') { Serial.println(pref.getString("log", "(nothing stored)")); for (;;) delay(1000); } delay(10); }
  pref.putString("log", "");
  int bad = 0; for (int i = 0; i < L_NIMG; i++) if (l_decide(i, 0) != L_EXPECT[i]) bad++;
  { char b[96]; snprintf(b, sizeof b, "LOGIC %s %d of %d\n", bad ? "FAIL" : "PASS", bad, L_NIMG); emit(b); }
  Wire.begin(21, 22); Wire.setClock(400000);
  if (!ina.begin()) { emit("ERROR INA219 not found (check SDA GPIO21, SCL GPIO22, VCC)\n"); for (;;) delay(1000); }
  xTaskCreatePinnedToCore(sampler, "samp", 4096, 0, 1, 0, 0);
  volatile int sink = 0;
  for (int r = 0; r < REPS; r++) {
    sum_ma[0] = sum_ma[1] = sum_v[0] = sum_v[1] = 0; ns[0] = ns[1] = 0;
    phase = 0; delay(PHASE_S * 1000);
    phase = 1; uint32_t t0 = micros(), n = 0;
    while (micros() - t0 < PHASE_S * 1000000UL) { for (int i = 0; i < L_NIMG; i++) sink += l_decide(i, 0); n += L_NIMG; }
    uint32_t dt = micros() - t0; phase = 0;
    char rb[200]; snprintf(rb, sizeof rb, "REP %d idle_mA %.3f run_mA %.3f bus_V %.3f decisions %lu run_s %.3f us_per_decision %.2f samples_idle %lu samples_run %lu\n",
      r, sum_ma[0] / ns[0], sum_ma[1] / ns[1], sum_v[1] / ns[1], (unsigned long)n, dt / 1e6, (float)dt / n, (unsigned long)ns[0], (unsigned long)ns[1]); emit(rb);
  }
  phase = 2; { char db[48]; snprintf(db, sizeof db, "DONE cpu_mhz %d\n", getCpuFrequencyMhz()); emit(db); }
}
void loop() { digitalWrite(2, !digitalRead(2)); delay(300); }
