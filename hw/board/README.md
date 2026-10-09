# SPARK on the Tang Nano 20K: board bring-up and power measurement

This folder puts `rtl/spark_core.v` on a Sipeed Tang Nano 20K (Gowin GW2AR-LV18QN88C8/I7), drives it over the onboard USB-UART, and measures board power with an ESP32 + INA219 logger.

| File | What it is |
|---|---|
| `uart_rx.v`, `uart_tx.v` | 8N1 UART, `CLK_HZ`/`BAUD` parameters (27 MHz / 115200 by default) |
| `spark_board_top.v` | Board top: power-on reset, UART command parser, `spark_core` (weights preloaded from hex), LEDs, marker pin |
| `tangnano20k.cst` | Pin constraints. **Lines marked TODO must be checked against the Sipeed wiki and schematic** |
| `tb_board.v` | Testbench: bit-level UART model, sends config and tokens, and checks every reply against a second, directly driven core |
| `esp32_ina219_logger/` | Arduino sketch: INA219 → CSV over USB serial, with a trigger input on GPIO4 |
| `host_bench.py` | Host script: runs configs, records per-token results, reads the power log, computes energy per token. `--dry-run` uses the golden model |

> **Fit warning.** `hw/results/synthesis.md` reports that the full core does not yet fit the GW2AR-18. Check the current utilisation (and the place-and-route result) before you order hardware or start the steps below. The core is still being edited in `rtl/spark_core.v`.

## 1. UART protocol (115200 8N1)

| Host sends | Meaning | Board replies |
|---|---|---|
| `C0 f capL capH t0 t1 t2 t3 conf` | Set config. `f`: bit0 sparse, bit1 delta, bit2 exit, bit3 recall, bit4 adapt. `cap` is u16 little-endian (0 = off). `exit_th` is s32 little-endian. `conf` = conf_th (0..3) | `C1` |
| `D0 b` | Run one token (input byte `b`) | 7 bytes: `pred, path, cyc0, cyc1, cyc2, cyc3, chk`. `cyc` = `tok_cycles` (u32 LE). `chk` = XOR of the first 6 bytes |
| `E0` | Ping | `5A` |
| `A0` / `A1` | Marker pin (`trig_out`) low / high | echo `A0` / `A1` |

- Defaults after power-up: sparse=1, all other switches off, cap=0, exit_th=64, conf_th=1. The fixed neuron constants are a=230, acc_sh=2 and s_sh=4, the same as in `rtl/spark_top.v`.
- Wait for each reply before you send the next command. The board drops bytes that arrive while a token is running or a reply is being sent.
- Core state persists across tokens and across config changes: the context, the recall table and the accumulators all live in BRAM. Only reloading the bitstream clears it. For an exact golden check, reprogram the board before a benchmark session.
- LEDs (active low):
  - LED0 toggles on every token.
  - LED1 is on while a token is running (busy).
  - LED2 shows the marker.
  - LED3 is a heartbeat (about 0.8 Hz).
  - LED4 toggles on every byte received.
  - LED5 toggles on every config received.
- Hold button S1 to reset the core and the UART logic.

## 2. Simulate first

```
cd hw/build        # needs emb.hex, w0..w3.hex, stim.hex (see below if missing)
iverilog -g2012 -o board.vvp ../rtl/spark_ram.v ../rtl/spark_core.v ../board/uart_rx.v \
    ../board/uart_tx.v ../board/spark_board_top.v ../board/tb_board.v && vvp -n board.vvp
```

The simulation takes about 30 s and ends with `PASS: 120 tokens over UART ...`. It overrides the UART timing to 1 MHz / 100 kbaud (10 clocks per bit) to run faster. `+ntok=N` changes the number of tokens per config. If the hex files are missing, generate them:

```
cd hw/build && python3 -c "import sys; sys.path.insert(0,'../golden'); import spark_golden as sg; sg.Weights().export_hex('.'); open('stim.hex','w').write('\n'.join(f'{b:02x}' for b in sg.stim_text())+'\n')"
```

Test the host script without a board:

```
python3 hw/board/host_bench.py --dry-run --repeats 2 --idle-s 0.2
```

In dry-run mode the golden model stands in for the FPGA. Power is **simulated** and labelled as such in every output.

## 3. Build the bitstream

`$readmemh` paths are relative to the directory you run yosys in. Run yosys from `hw/build`, where the hex files are, or pass absolute paths through the `EMB_HEX`/`W0_HEX`..`W3_HEX` parameters (`chparam`).

### Open-source flow (Yosys + nextpnr + Apicula)

```
cd hw/build
yosys -p "read_verilog ../rtl/spark_ram.v ../rtl/spark_core.v ../board/uart_rx.v ../board/uart_tx.v ../board/spark_board_top.v; \
          synth_gowin -top spark_board_top -json board.json"

# current nextpnr (himbaechel):
nextpnr-himbaechel --json board.json --write board_pnr.json \
    --device GW2AR-LV18QN88C8/I7 --vopt family=GW2A-18C --vopt cst=../board/tangnano20k.cst --freq 27
# or legacy nextpnr-gowin:
# nextpnr-gowin --json board.json --write board_pnr.json --device GW2AR-LV18QN88C8/I7 \
#     --family GW2A-18C --cst ../board/tangnano20k.cst --freq 27

gowin_pack -d GW2A-18C -o board.fs board_pnr.json
openFPGALoader -b tangnano20k board.fs          # SRAM (volatile). Add -f to write flash
```

You need a recent nextpnr built with the himbaechel Gowin arch, plus a matching Apicula (`pip install apycula`); the OSS CAD Suite nightly has both. Distro packages such as Debian/Ubuntu `nextpnr-gowin` 0.6 ship only GW1N chip databases and reject the GW2AR-18.

Read the nextpnr timing report (`Max frequency for clock 'clk'`). If it is below 27 MHz, choose one of these fixes:
- Add a PLL (Gowin `rPLL`) for a lower core clock and set `CLK_HZ` to match.
- Pipeline the core.

The `cyc` counts stay valid either way, but the wall time per token changes.

### Gowin EDA (GUI) alternative

1. Create a new project. Device: GW2AR-LV18QN88C8/I7 (Tang Nano 20K).
2. Add the five `.v` files, set `spark_board_top` as top and add `tangnano20k.cst`.
3. Copy the `.hex` files into the project directory, or set the hex parameters to absolute paths.
4. In Project → Configuration → Dual-Purpose Pin, tick "Use SSPI as regular IO" and "Use MSPI as regular IO" if the tool complains about pins.
5. Run Synthesize and then Place & Route.
6. Program with the Gowin Programmer or with `openFPGALoader -b tangnano20k impl/pnr/*.fs`.

### Find the UART

The BL616 shows up as two serial ports: JTAG/debug and UART. On Linux these are usually `/dev/ttyUSB0` and `/dev/ttyUSB1`, and the UART is normally the second one. Check it with a ping: send `E0` and expect `5A`. You can also run `host_bench.py --port ... --configs event --repeats 1`.

## 4. Power measurement wiring

```
 Host USB 5V ──► [USB breakout / cut cable: red +5V wire] ──► INA219 VIN+
                                                               INA219 VIN- ──► +5V into Tang Nano 20K USB-C
 Host USB GND ───────────────────────────────── (passes straight through) ──► Tang Nano GND
 USB D+/D- ──────────────────────────────────── (pass straight through, so the UART still works)

 ESP32 3V3 ──► INA219 VCC          ESP32 GPIO21 ──► INA219 SDA
 ESP32 GND ──► INA219 GND          ESP32 GPIO22 ──► INA219 SCL
 ESP32 GND ──► Tang Nano GND (common ground; needed for the trigger wire)
 Tang Nano trig_out (header pin, see .cst TODO) ──► ESP32 GPIO4   (optional; 3.3 V logic)
 ESP32 USB ──► host (second serial port, 921600 baud CSV)
```

- The INA219 sits in the high side of the Tang Nano's 5 V supply only, so the ESP32's own power is not measured.
- A USB-C "power meter / data pass-through" breakout with exposed VBUS pads, or a USB cable with its red wire cut, both work. Keep D+/D- and GND intact.
- The breakout's 0.1 Ω shunt drops about 15 mV at 150 mA, so the board sees roughly 4.98 V. That is negligible.
- `host_bench.py` also writes `M1`/`M0` over the logger's serial port, so the trigger wire is optional. The CSV column `mark` shows the software marker and `trig` shows the wire.
- Sample rate: about 1–2 kHz rows (about 0.9 kHz independent INA219 conversions in 12-bit mode). With `AVG_MODE 1` it is about 15 Hz with 128× hardware averaging. Either is fine for runs of 10 s or more.

## 5. Measurement protocol

1. **Program the board fresh.** This clears the BRAM state and keeps the golden check exact.
2. **Warm-up.** Leave the board powered and configured for 5 minutes so the regulators and the FPGA die reach a steady temperature. The script also runs 32 warm-up tokens per repeat.
3. **Record the ambient temperature** with `--ambient-c`. Optionally attach a DS18B20, or a thermocouple with Kapton tape, to the top of the FPGA package and log it alongside. Leakage power depends on temperature.
4. **Idle baseline.** Before every repeat, the script measures `--idle-s` seconds (default 10) with the board configured and no tokens running.
5. **Run.** It streams the text, repeating whole passes until at least `--min-run-s` (default 10 s), with the marker on.
6. **Repeat.** It does 5 repeats per config (`--repeats 5`) and reports mean ± sample std.
7. **Configs.** Run `--configs dense,event,adaptive,uart-control`. The `uart-control` config sends pings at the same rate with no inference, which measures the USB/UART traffic cost.

```
python3 hw/board/host_bench.py --port /dev/ttyUSB1 --power-port /dev/ttyUSB2 \
    --text some_code.py --configs dense,event,adaptive,uart-control \
    --repeats 5 --idle-s 10 --min-run-s 10 --ambient-c 24.0
```

Outputs go to `hw/results/board_<timestamp>/`:
- `runs.csv`: one row per config × repeat.
- `tokens.csv`: per token pred/path/cycles/wall µs.
- `summary.md`.

## 6. Computing energy per token

For a run of `N` tokens lasting `T` seconds, with mean board power `P_run` and idle baseline `P_idle`:

- `E_total / token = P_run · T / N`: whole-board energy per token.
- `E_above / token = (P_run − P_idle) · T / N`: energy above idle.
- `E_core ≈ E_above(config) − E_above(uart-control)`: an estimate of the inference cost alone. It is noisy, so report its spread.
- `cycles / token` comes from the core's own counter. `core time / token = cycles / 27 MHz`. Compare configs by both cycles and energy.

## 7. Honesty notes

- **Board power is not FPGA power.** The 5 V input feeds:
  - the BL616 USB bridge (a whole RISC-V MCU),
  - the LDO/DC-DC regulators, LEDs and SDRAM-in-package,
  - the FPGA.

  Idle board power is typically hundreds of mW. The FPGA's dynamic power for this core may be a few mW, which is near the INA219's noise floor (0.01 mV shunt LSB = 0.1 mA = 0.5 mW at 5 V). Always report **both** total and above-idle numbers, and state the noise (std over repeats).
- At 115200 baud the UART and USB round trip (≈1 ms or more per token) dominates the wall time. The core itself runs in microseconds. "Tokens per second" here measures the link, not the core.
- The weights are random demo weights, so `pred` is not a meaningful language prediction. The results show work and energy differences between configs, plus bit-exact agreement with the golden model.
- LEDs toggling per token add a small amount of switching current. It is the same for every config.

## 8. Uncertain items (check before use)

- **Pins** (see `tangnano20k.cst`).
  - Assumed: clock on pin 4, UART TX/RX on 69/70, LEDs on 15–20, S1/S2 on 88/87.
  - Button polarity is assumed to be "pressed = 1". If S1 reads 0 when pressed, the design stays in reset (all LEDs dark, no heartbeat). Invert `btn_s1` in that case.
  - The `trig_out` pin (76) is a **guess**. Pick a free header pin from the wiki pinout.
- **IO voltage.** The `IO_TYPE=LVCMOS33` banks are assumed to be 3.3 V. Check the bank voltages in the schematic.
- **Dual-purpose pins.** Check whether pins 69/70 need the dual-purpose pin options in Gowin EDA.
- **ESP32 boards differ.** Use the GPIO numbers that your dev board actually breaks out. Some boards cannot use `INPUT_PULLDOWN` on certain pins.
