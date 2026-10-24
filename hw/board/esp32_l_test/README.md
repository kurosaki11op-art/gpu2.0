# ESP32 test of the L decision (logic + speed + power)

**Check on a PC:** `gcc -Iesp32_l_test host_check.c -o host_check && ./host_check`.

**What is verified here (cloud, no ESP32 available):** `host_check.c` compiles the exact decision code (`esp32_l_test/l_decide.h`) with gcc and compares 200 clothing images with the Python integer model: result: 0 of 200 differ, LOGIC PASS. The table is the trained slow table (10 x 4,608, signed 8-bit, 46 KB), single view, 88.85% on the whole test set.

**What only you can do (needs the board):**
1. Arduino IDE (or PlatformIO), board "ESP32 Dev Module"; open `esp32_l_test/esp32_l_test.ino` (the copies of `l_decide.h` and `l_table.h` sit beside it); upload; serial monitor 115200.
2. Expect `LOGIC PASS` and a `RUN ... us each` line every few seconds. Send me that line.
3. Power: wire an INA219 in series with the ESP32 supply (wiring in `../README.md`, logger `../esp32_ina219_logger`). GPIO4 is high during the decision loop. Record current idle (same sketch, `delay` only) and during the loop; energy per decision = (P_loop - P_idle) x time per decision. Use a USB power bank, Wi-Fi/Bluetooth off.

**Honest scope:** the ESP32 is a general-purpose processor running the lookup-and-add rule in software, so its energy per decision says nothing about the L chip; it only proves the logic runs on another machine and gives a real measured baseline for "lookup-and-add on a cheap MCU" to compare with a GPU doing the same task. Regenerate the table with `hw/brain/experiments/month5/export_esp32.py`.

## End-to-end procedure (one ESP32 + one INA219, ready to run)

Everything below is prepared and checked on a PC (sketch compiles and runs against a mock board, LOGIC PASS; the analysis script was tested on made-up numbers, not data). Nothing has been measured on a board yet.

1. **Wire** (5 minutes): USB 5V -> INA219 VIN+; INA219 VIN- -> ESP32 VIN (5V) pin; grounds common; INA219 VCC -> ESP32 3V3, SDA -> GPIO21, SCL -> GPIO22. Power the ESP32 from a USB power bank or a clean USB port. Do not connect anything else to the ESP32 (no Wi-Fi, no Bluetooth: the sketch never starts them).
2. **Flash** `esp32_l_selftest/esp32_l_selftest.ino` (Arduino IDE, board ESP32 Dev Module, library "Adafruit INA219"). The folder already holds `l_decide.h` and `l_table.h`.
3. **Run:** open the serial monitor at 115200 and let it finish (about 70 s: 5 repetitions of 6 s idle + 6 s decisions). Save the text to `run1.txt`. Expect `LOGIC PASS 0 of 200`, five `REP` lines and `DONE`.
4. **Check:** `python3 check_esp32_run.py run1.txt --ambient-c 25` prints speed (us per decision), idle and run current, delta power, and energy per decision (delta and total) as mean +- std, plus a verdict (UNRELIABLE if idle drifts more than 3% or the signal is under 3x its spread).
5. **Do it three times**: once after 5 minutes warm-up, again after changing the clock (`setCpuFrequencyMhz(80)` and `(160)` at the top of `setup()`), so we also see energy per decision against clock speed. Send me the three log files.
6. **Record:** I add them to `hw/results/` as MEASURED with the script output.

How the measurement works and why it is trustworthy: core 0 samples the INA219 all the time in both phases (its own load cancels in the difference); core 1 sleeps (idle phase) or does L decisions (run phase). Energy per decision (delta) = (run power - idle power) / decisions per second. Limits: INA219 resolution about 0.1 mA, 12-bit conversions of about 0.5 ms each, power of the INA219 and USB cable losses fixed in both phases; temperature drift is why the board is warmed up first. The result is the energy of a cheap microcontroller running the lookup-and-add rule in software; it is a real baseline, not the energy of the L chip.

Prompt for another assistant to guide the run: [CHATGPT_PROMPT.md](CHATGPT_PROMPT.md).

## Minimum parts and the no-adapter procedure (updated 24 Oct)

Electronic parts: **one ESP32 Dev Module and one INA219 module.** Also needed, but ordinary: about 8 jumper wires (or thin wire), a USB phone charger or power bank, and one old USB cable you can cut (to bring the 5V red wire to the INA219). No USB-to-serial adapter: the updated `esp32_l_selftest` saves its results in the ESP32's flash.

1. Flash `esp32_l_selftest.ino` over the normal USB cable.
2. Unplug it. Wire USB charger 5V (cut cable, red wire) to INA219 VIN+, INA219 VIN- to the ESP32 VIN pin, grounds together, INA219 VCC to 3V3, SDA to GPIO21, SCL to GPIO22.
3. Power the charger. After 8 s the test starts by itself (about 70 s); the blue LED (GPIO2) blinks when it is done.
4. Power off. Plug the normal USB cable into the laptop, open the Serial Monitor at 115200, press EN (reset) and type `s` within 8 s: the saved lines (`LOGIC`, `REP`..., `DONE`) are printed. Copy them to `run1.txt` and run `python3 check_esp32_run.py run1.txt`.

Checked on a PC against a mock board (compiles; LOGIC PASS; the current readings are stubs there, so nothing measured yet).

Related: [Board README](../README.md), [Hardware index](../../HARDWARE_INDEX.md)
