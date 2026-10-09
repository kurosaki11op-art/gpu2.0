// esp32_ina219_logger.ino -- INA219 power logger for SPARK board measurements.
//
// Hardware: any ESP32 dev board (ESP32-WROOM / DevKitC) + INA219 breakout
// (Adafruit or clone, 0.1 ohm shunt). Library: "Adafruit INA219" (Library Manager).
//
// Wiring (see hw/board/README.md for the full diagram):
//   INA219 VCC -> ESP32 3V3        INA219 GND -> ESP32 GND -> Tang Nano GND (common!)
//   INA219 SDA -> ESP32 GPIO21     INA219 SCL -> ESP32 GPIO22
//   INA219 VIN+ <- +5 V from the USB supply (host/USB power meter side)
//   INA219 VIN- -> +5 V into the Tang Nano 20K (cut USB cable red wire or a
//                  USB breakout pair); GND of the USB cable passes straight through.
//   ESP32 GPIO4 <- trigger/marker (FPGA trig_out pin, 3.3 V logic, optional)
//
// Output: CSV over USB serial at 921600 baud, one row per sample:
//   t_ms,t_us,bus_V,shunt_mV,current_mA,power_mW,trig,mark
// bus_V is measured at VIN- (the board side). current = shunt_mV / R_SHUNT.
// power_mW = bus_V * current_mA. trig = GPIO4 level, mark = software marker.
// Lines starting with '#' are comments/events (the host ignores them).
//
// Sample rate: the INA219 in its default 12-bit, no-averaging mode converts
// shunt and bus in ~532 us each, so it produces ~940 NEW samples/s; this loop
// reads two registers over 400 kHz I2C (~0.25 ms) and prints ~55 bytes per row,
// so expect roughly 1-2 kHz rows, with consecutive rows sometimes repeating the
// same conversion (~0.9-1 kHz of independent data). Set AVG_MODE = 1 for
// 128-sample hardware averaging (~68 ms per sample, ~15 Hz, much less noise);
// for energy integration over multi-second runs either mode works.
//
// Serial commands from the host (newline-terminated):
//   M1 / M0  set / clear the software marker column (benchmark start/stop)
//   R        reset the time origin (t_ms/t_us restart at 0)
//   P        pause streaming,   S  resume streaming
// micros() wraps after ~71 minutes; keep each logging session shorter than that
// or use t_ms.

#include <Wire.h>
#include <Adafruit_INA219.h>

#define SDA_PIN   21
#define SCL_PIN   22
#define TRIG_PIN  4
#define R_SHUNT   0.1f       // ohm; check the resistor on your breakout (R100 = 0.1)
#define AVG_MODE  0          // 0: fastest (12-bit, 1 sample), 1: 128x averaging
#define BAUD      921600

Adafruit_INA219 ina219;
uint32_t t0_us = 0, t0_ms = 0;
bool streaming = true;
int mark = 0;
char cmd[16];
uint8_t cmd_len = 0;

static void ina_write16(uint8_t reg, uint16_t v) {
  Wire.beginTransmission(0x40);   // default INA219 address (A0 = A1 = GND)
  Wire.write(reg);
  Wire.write(v >> 8);
  Wire.write(v & 0xFF);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(BAUD);
  pinMode(TRIG_PIN, INPUT_PULLDOWN);
  Wire.begin(SDA_PIN, SCL_PIN);
  if (!ina219.begin(&Wire)) {
    while (true) { Serial.println("# ERROR: INA219 not found at 0x40"); delay(1000); }
  }
  Wire.setClock(400000);
  // 32 V / 1 A calibration: covers a Tang Nano 20K (typically 0.1-0.3 A at 5 V)
  // with 0.04 mA current LSB. We compute current from the shunt voltage anyway.
  ina219.setCalibration_32V_1A();
  // Config register (0x00): BRNG=32V, PGA=/8 (320 mV), ADC modes, continuous
  // shunt+bus. Bits: BRNG[13] PG[12:11] BADC[10:7] SADC[6:3] MODE[2:0].
  uint16_t adc = AVG_MODE ? 0xF : 0x3;          // 0x3: 12-bit 532 us, 0xF: 128 avg 68 ms
  uint16_t cfg = (1u << 13) | (3u << 11) | (adc << 7) | (adc << 3) | 0x7;
  ina_write16(0x00, cfg);
  t0_us = micros(); t0_ms = millis();
  Serial.println("# esp32_ina219_logger v1");
  Serial.printf("# R_SHUNT=%.3f AVG_MODE=%d\n", R_SHUNT, AVG_MODE);
  Serial.println("t_ms,t_us,bus_V,shunt_mV,current_mA,power_mW,trig,mark");
}

static void handle_cmd() {
  cmd[cmd_len] = 0;
  if (cmd[0] == 'M') { mark = (cmd[1] == '1'); Serial.printf("# mark %d\n", mark); }
  else if (cmd[0] == 'R') { t0_us = micros(); t0_ms = millis(); Serial.println("# time reset"); }
  else if (cmd[0] == 'P') { streaming = false; Serial.println("# paused"); }
  else if (cmd[0] == 'S') { streaming = true; Serial.println("t_ms,t_us,bus_V,shunt_mV,current_mA,power_mW,trig,mark"); }
  cmd_len = 0;
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (cmd_len) handle_cmd(); }
    else if (cmd_len < sizeof(cmd) - 1) cmd[cmd_len++] = c;
  }
  if (!streaming) return;
  uint32_t tus = micros() - t0_us, tms = millis() - t0_ms;
  float shunt_mV = ina219.getShuntVoltage_mV();
  float bus_V = ina219.getBusVoltage_V();
  float current_mA = shunt_mV / R_SHUNT;            // mV / ohm = mA
  float power_mW = bus_V * current_mA;
  int trig = digitalRead(TRIG_PIN);
  Serial.printf("%lu,%lu,%.4f,%.3f,%.2f,%.1f,%d,%d\n",
                (unsigned long)tms, (unsigned long)tus, bus_V, shunt_mV,
                current_mA, power_mW, trig, mark);
}
