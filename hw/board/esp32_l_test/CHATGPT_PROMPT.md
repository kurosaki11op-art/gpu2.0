# Prompt to give another assistant for the ESP32 Dev Module test

Copy everything between the lines into the chat. Attach (or paste) these files from the repo folder `hw/board/esp32_l_test/`: `esp32_l_selftest/esp32_l_selftest.ino`, `esp32_l_selftest/l_decide.h`, `esp32_l_selftest/l_table.h`, `check_esp32_run.py`. (`l_table.h` is about 700 KB; if the chat cannot take it, say so and use the repo link.)

---
I have an ESP32 Dev Module (ESP32-WROOM), an INA219 current-sensor breakout (0.1 ohm shunt), a USB cable, jumper wires, a Windows/Mac/Linux laptop. I want to run a prepared test and send back the results. Guide me one small step at a time, wait for my reply after each step, and do not skip steps. Do not change the test logic.

What the test is: the sketch `esp32_l_selftest.ino` runs a lookup-and-add classifier (10 classes x 4,608 inputs, signed 8-bit table, no multiplication) on the ESP32, first checks that 200 test images give the same answers as a reference model (it prints `LOGIC PASS 0 of 200`), then measures speed (microseconds per decision) and the board's current with the INA219 over 5 repetitions of 6 seconds idle and 6 seconds running. A Python script `check_esp32_run.py` turns the saved serial text into speed, power and energy per decision.

Please walk me through:
1. Installing Arduino IDE 2.x, the "esp32 by Espressif Systems" board package (Boards Manager) and the "Adafruit INA219" library (accept the BusIO dependency). Select board "ESP32 Dev Module" and the correct port; tell me how to find the port and fix "port busy" or driver (CP210x / CH340) problems.
2. FIRST, logic and speed only, with no INA219 wired: put the three files in a folder named exactly `esp32_l_selftest`, open the .ino, upload (compile takes 1 to 2 minutes because the table is large), open Serial Monitor at 115200. I expect `LOGIC PASS 0 of 200` and then `ERROR INA219 not found`, which is correct at this stage. If I see `LOGIC FAIL` or a compile error, help me find the cause; do not edit the table file.
3. Then wire for power (confirm each connection with me before I power it): USB 5V -> INA219 VIN+; INA219 VIN- -> ESP32 VIN (5V) pin; ESP32 GND -> INA219 GND; INA219 VCC -> ESP32 3V3; INA219 SDA -> GPIO21; INA219 SCL -> GPIO22. Power the ESP32 only through this path, from a USB power bank or a clean USB port (no second USB cable on the ESP32 while measuring, because it would bypass the sensor; so for the serial output tell me how to read the data safely, for example by uploading first, then unplugging the data cable and powering via the sensor path with a USB-to-serial adapter on TX0/RX0 and GND, or by using a laptop USB port for the 5V feed and reading serial from the same cable only if the sensor sits in series on that 5V line).
4. Re-upload nothing; reset the board, wait about 70 seconds for `DONE`, and have me save the full Serial Monitor text as `run1.txt`.
5. Run `python3 check_esp32_run.py run1.txt --ambient-c <room temperature>` and have me paste the whole output.
6. Repeat the run after a 5 minute warm-up, and again with the CPU clock changed by adding `setCpuFrequencyMhz(160);` (then `80`) as the first line of `setup()`, saving `run2.txt`, `run3.txt` and so on. Tell me how many runs are enough to trust the numbers (at least 3 per clock setting) and what to do if the script says UNRELIABLE.
7. At the end, give me one summary table to send to my team: clock MHz, microseconds per decision, idle mA, run mA, delta power mW, energy per decision (delta and total, microjoules), verdict, plus any problem I hit.

Rules: use plain words, keep each answer short, say when something I report looks wrong (for example run current below idle, or an INA219 reading that is zero), and never invent numbers I did not give you.
---

After the run, send the files `run*.txt` and the summary table back to me (Claude) and I will record them as MEASURED.

Related: [ESP32 test README](README.md), [Hardware index](../../HARDWARE_INDEX.md)
