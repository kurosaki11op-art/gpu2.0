# ESP32 test of the L decision (logic + speed + power)

**Check on a PC:** `gcc -Iesp32_l_test host_check.c -o host_check && ./host_check`.

**What is verified here (cloud, no ESP32 available):** `host_check.c` compiles the exact decision code (`esp32_l_test/l_decide.h`) with gcc and compares 200 clothing images with the Python integer model: result: 0 of 200 differ, LOGIC PASS. The table is the trained slow table (10 x 4,608, signed 8-bit, 46 KB), single view, 88.85% on the whole test set.

**What only you can do (needs the board):**
1. Arduino IDE (or PlatformIO), board "ESP32 Dev Module"; open `esp32_l_test/esp32_l_test.ino` (the copies of `l_decide.h` and `l_table.h` sit beside it); upload; serial monitor 115200.
2. Expect `LOGIC PASS` and a `RUN ... us each` line every few seconds. Send me that line.
3. Power: wire an INA219 in series with the ESP32 supply (wiring in `../README.md`, logger `../esp32_ina219_logger`). GPIO4 is high during the decision loop. Record current idle (same sketch, `delay` only) and during the loop; energy per decision = (P_loop - P_idle) x time per decision. Use a USB power bank, Wi-Fi/Bluetooth off.

**Honest scope:** the ESP32 is a general-purpose processor running the lookup-and-add rule in software, so its energy per decision says nothing about the L chip; it only proves the logic runs on another machine and gives a real measured baseline for "lookup-and-add on a cheap MCU" to compare with a GPU doing the same task. Regenerate the table with `hw/brain/experiments/month5/export_esp32.py`.

Related: [Board README](../README.md), [Hardware index](../../HARDWARE_INDEX.md)
