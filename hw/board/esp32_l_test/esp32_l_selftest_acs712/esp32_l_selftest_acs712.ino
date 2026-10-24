// ESP32 self-measuring L test with an ACS712 (analog Hall current sensor) instead of an INA219. LOW-CONFIDENCE power measurement: see README.
// Wiring: 5V source (charger/power bank, cut USB cable red wire) -> ACS712 screw terminal IP+ ; terminal IP- -> ESP32 VIN pin ;
//         ACS712 VCC <- the same 5V source (upstream of the terminal, so the module's own current is NOT counted) ; ACS712 GND, ESP32 GND, source GND all joined ;
//         ACS712 OUT -> ESP32 GPIO34 (ADC1, input only). 5A version assumed: 185 mV per A (20A: 100, 30A: 66; set SENS_MV_PER_A in the analysis script).
// Method: core 0 samples GPIO34 as fast as it can (calibrated millivolts) in every phase; core 1 sleeps (IDLE) or runs L decisions (RUN).
//   Only the DIFFERENCE of the mean output between RUN and IDLE is used (offset and its drift cancel): delta_mA = (run_mV - idle_mV) / sens.
// No USB during the run. At boot wait 8 s for 's' on USB serial: if received, print the results saved in flash and stop. Otherwise run, save, blink GPIO2.
#include <Preferences.h>
#include "l_decide.h"
#define ADC_PIN 34
#define PHASE_S 8
#define REPS 6
Preferences pref; String logbuf;
static void emit(const String &l) { Serial.print(l); logbuf += l; pref.putString("log", logbuf); }
volatile int phase = 0;                 // 0 idle, 1 run, 2 stop
volatile double s1[2] = {0, 0}, s2[2] = {0, 0}; volatile uint32_t ns[2] = {0, 0};
static void sampler(void *) {
  for (;;) {
    int p = phase;
    if (p < 2) { double v = analogReadMilliVolts(ADC_PIN); s1[p] += v; s2[p] += v * v; ns[p]++; } else vTaskDelay(10);
    if ((ns[0] & 1023) == 1023) vTaskDelay(1);                 // keep the watchdog happy
  }
}
void setup() {
  Serial.begin(115200); pref.begin("ltest", false); pinMode(2, OUTPUT);
  uint32_t tw = millis(); while (millis() - tw < 8000) { if (Serial.available() && Serial.read() == 's') { Serial.println(pref.getString("log", "(nothing stored)")); for (;;) delay(1000); } delay(10); }
  pref.putString("log", ""); logbuf = "";
  int bad = 0; for (int i = 0; i < L_NIMG; i++) if (l_decide(i, 0) != L_EXPECT[i]) bad++;
  { char b[96]; snprintf(b, sizeof b, "LOGIC %s %d of %d\n", bad ? "FAIL" : "PASS", bad, L_NIMG); emit(b); }
  analogSetPinAttenuation(ADC_PIN, ADC_11db);
  xTaskCreatePinnedToCore(sampler, "samp", 4096, 0, 1, 0, 0);
  volatile int sink = 0;
  for (int r = 0; r < REPS; r++) {
    s1[0] = s1[1] = s2[0] = s2[1] = 0; ns[0] = ns[1] = 0;
    phase = 0; delay(PHASE_S * 1000);
    phase = 1; uint32_t t0 = micros(), n = 0;
    while (micros() - t0 < PHASE_S * 1000000UL) { for (int i = 0; i < L_NIMG; i++) sink += l_decide(i, 0); n += L_NIMG; }
    uint32_t dt = micros() - t0; phase = 0;
    double mi = s1[0] / ns[0], mr = s1[1] / ns[1], si = sqrt(fmax(0.0, s2[0] / ns[0] - mi * mi)), sr = sqrt(fmax(0.0, s2[1] / ns[1] - mr * mr));
    char rb[240]; snprintf(rb, sizeof rb, "REP %d idle_mV %.3f run_mV %.3f sd_idle %.2f sd_run %.2f n_idle %lu n_run %lu decisions %lu run_s %.3f us_per_decision %.2f\n",
      r, mi, mr, si, sr, (unsigned long)ns[0], (unsigned long)ns[1], (unsigned long)n, dt / 1e6, (float)dt / n); emit(rb);
  }
  phase = 2; { char db[48]; snprintf(db, sizeof db, "DONE cpu_mhz %d\n", getCpuFrequencyMhz()); emit(db); }
}
void loop() { digitalWrite(2, !digitalRead(2)); delay(300); }
