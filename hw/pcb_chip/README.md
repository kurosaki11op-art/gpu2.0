# SPARK chip evaluation board (KiCad 7) — v0.1

Board for the packaged SKY130 SPARK chip (`hw/rtl/spark_chip.v`, QFN-32 package plan in `gen_symbol.py`).

- USB-C (J1) → AP2112K-3.3 (U3) → AP2112K-1.8 (U4) → **0.1 Ω shunt (RS1) → chip core rail VCCD**;
  INA219 (U5) measures the chip's own core current and voltage (I2C on J2).
- CH340C (U2) bridges USB to the chip UART (the same protocol the testbench uses).
- 27 MHz oscillator (Y1) → 22 Ω → CLK; RST_N with 10 k pull-up, 1 µF and a reset button (SW1).
- LEDs on READY / BUSY / TOK; J2 = ESP32 logger header (3V3, GND, SDA, SCL, TRIG, TOK); J3 = debug UART.
- 4× 100 nF + 10 µF on each supply at the chip; test points on VCCD, 3V3, GND, CLK.

| Check | Result |
|---|---|
| Schematic connectivity + rules (KiCad netlist export, `verify_sch.py`) | 163 pins, 43 nets, **0 errors** (one documented waiver: CH340C V3 tied to VCC at 3.3 V, per datasheet) |
| KiCad DRC (`run_drc.py`) | **0 errors, 0 warnings, 0 unconnected** |
| PCB ↔ schematic parity | 168 pads, **0 mismatches** |

60 × 46 mm, 2 layers, Freerouting + GND pours. Chip rails use 0.25 mm tracks to reach the 0.5 mm-pitch QFN pins.
Limits: the SPARK chip package/pinout is our plan (the die pad ring is not designed yet); not manufactured or tested.
