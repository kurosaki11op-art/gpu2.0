# L on the Tang Nano 20K: board bring-up and power measurement

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

---

# L-lookup (lookup-only core) on the Tang Nano 20K

This section is for the lookup-only core `rtl/lookup/spark_lookup2.v`: no matrices, no multipliers, no weights.
It uses the same pins as above: `tangnano20k.cst` works unchanged, and its TODO lines still need checking against the Sipeed wiki.

| File | What it is |
|---|---|
| `lookup_board_top.v` | Board top: power-on reset, UART command parser, a 16-byte reply FIFO, counters, `spark_lookup2` core |
| `tb_lookup_board.v`, `check_lookup_board.py` | End-to-end simulation through a bit-level UART model; every reply byte is checked against the reference model |
| `host_lookup.py` | PC script: streams a file through the board, checks every prediction bit-exactly against the reference, reads the board's own accuracy counters. `--dry-run` works without a board |
| `../rtl/lookup/conf_lut.hex` | Initial confidence table (32 entries), loaded at configuration |

## Protocol (115200 8N1)

| Host sends | Board replies |
|---|---|
| `E0` | `5A` (after the power-on table clear) |
| `D1 b` | `pred, flags, conf, chk` (flags: bit0 hit, bits 3:1 source, bits 5:4 count; chk = XOR of the three) |
| `D2 n b1..bn` (n <= 255) | n predictions, then the XOR of them |
| `F0` | bytes, correct, hits (3 x u32 little-endian), XOR checksum |
| `C2 a v` | `C3` (confidence entry a = v) |
| `B0` | `B1` once the tables and counters are cleared |
| `A0` / `A1` | echo (marker pin `trig_out` low / high, for the power logger) |

## Status (SIMULATED)

- `python check_lookup_board.py` (from `hw/board`): **436 reply bytes, 0 mismatches**, 0 UART framing errors. It covers ping, 40 single-byte predictions, a 200-byte stream, the counters, a run-time confidence write, clear and the marker.
- yosys `synth_gowin` of the whole board design (TB = 11), with no place-and-route: **25 of 46 block RAMs (54%), about 2,650 LUT cells (13%), about 610 flip-flops (4%)**. Timing and power are not yet measured.
- `host_lookup.py --dry-run` on 20,000 prose bytes: 0 mismatches against the reference, 49.75% next-byte accuracy, matching the simulation.

## Build and run (to do on the PC)

1. **Gowin IDE** (vendor tool, which gives timing and power reports):
   - New project, device GW2AR-LV18QN88C8/I7.
   - Add `rtl/lookup/spark_lookup2.v`, `board/uart_rx.v`, `board/uart_tx.v`, `board/lookup_board_top.v` and `board/tangnano20k.cst`.
   - Set the top module to `lookup_board_top`.
   - Copy `rtl/lookup/conf_lut.hex` into the project folder, or set the `CONF_HEX` parameter to its full path.
   - Run synthesis and place-and-route, then save the timing report and the power report.
2. **Program the board:** Gowin Programmer, or `openFPGALoader -b tangnano20k <project>.fs`.
3. **Run:** `pip install pyserial`, find the COM port in Device Manager, then:
   `py -3.12 hw\board\host_lookup.py --port COMx --file hw\system\data\prose_slices.txt --max-bytes 20000`
   - It should report 0 mismatches.
   - It should report about the same accuracy as the dry run on the same file.
   - It should report about 11,000 bytes/s, which is the UART limit. The core itself runs at about 5 cycles per byte.
4. **If nothing answers:** check the pin TODOs in `tangnano20k.cst` (UART pins 69/70, and the reset-button polarity).

# L Cortex (the brain core that keeps learning) on the Tang Nano 20K

Files: `cortex_board_top.v` (top, same pins as above, so `tangnano20k.cst` works unchanged), `../rtl/cortex/cortex_core.v`
(core), `uart_rx.v`, `uart_tx.v`. Host: `cortex_host.py`. Checks: `check_cortex_board.py` (UART-level testbench vs
the integer chip model, 0 mismatches) and `../rtl/cortex/run_check_cortex.py` (core, 0 mismatches).

## Protocol (115200 8N1, one command at a time)

| Bytes sent | Meaning | Reply |
|---|---|---|
| `E0` | ping | `5A` |
| `53` + 128 bytes | seed the 32 random lanes (4 bytes each, little-endian) | `53` |
| `43` | clear table, dream counters, counts, known classes | `43` |
| `4B c` | mark class c known | `4B` |
| `4C c nl nh` + n x (lo hi) | LEARN one example of class c (its active code bits) | 1 if the table was written |
| `50 nl nh` + n x (lo hi) | PREDICT | class |
| `44 c` | DREAM one class-c example and practise on it | dream length lo, hi, 1 if the table was written |
| `45 n c1..cn` | DREAM BATCH: n dreams (0 = 256) of the listed classes, in order, each practised | surprises (2 bytes) |
| `54` + 512 bytes | load the 128 sensory detectors (4 bytes each, 25 bits used) | `54` |
| `49 c` + 784 bytes | IMAGE: the chip encodes a raw 28x28 image itself, then LEARNs it as class c (or PREDICTs if c = FF) | updated / class |
| `52 bl bh` | read memory word b (table 50 bits in 7 bytes, dream counts 100 bits in 13) | 20 bytes |
| `57 bl bh` + 20 bytes | write memory word b | `57` |
| `4E` | read example counts (13 bytes) and known classes (2 bytes) | 15 bytes |
| `4D` + 15 bytes | write them | `4D` |

## Status

- SIMULATED: core and board bit-exact with the integer chip model (0 mismatches).
- **Bitstream built** with the open-source flow (`hw/pnr_cortex/build.sh`: yosys + nextpnr-himbaechel + apicula):
  `hw/pnr_cortex/cortex_tangnano20k.fs.gz`, **including the on-chip sensory encoder** (`hw/rtl/cortex/cortex_encoder.v`,
  bit-exact with `Features.encode`: 0 mismatching images of 40 digits and 40 clothing images, ~21,400 cycles per image).
  Place and route (15 Oct, with dream batches, command 45): 46/46 block RAMs (100%), 18,522 LUT4 (89%), 5,364
  flip-flops (34%), 363/648 LUT-RAMs (the encoder's code map is packed 4 bits per word), 0 of the hardware
  multipliers; max clock 69.8 MHz (board clock 27 MHz); no hold violations (all block-RAM inputs are re-registered on
  the falling clock edge). The FPGA is nearly full: the unpacked version (94%) did not legalise.
- Without the encoder (PC sends codes): 11,223 LUT4 (54%), 68.6 MHz.
- Not yet done: a real board run (needs the user's board), power measurement.

## Run it (on the PC)

1. Ready-made bitstream: unzip `hw/pnr_cortex/cortex_tangnano20k.fs.gz` and program it with
   `openFPGALoader -b tangnano20k cortex_tangnano20k.fs` (SRAM, lost at power-off; add `-f` to write flash), or the
   Gowin Programmer. Check the pin TODOs in `tangnano20k.cst` against your board first (UART 69/70, clock 4, LEDs 15-20).
   To rebuild it yourself, use section 3 above with these files and top `cortex_board_top`:
   `yosys -p "read_verilog ../rtl/cortex/cortex_core.v ../board/uart_rx.v ../board/uart_tx.v ../board/cortex_board_top.v; synth_gowin -top cortex_board_top -json cortex.json"`,
   then nextpnr / gowin_pack / openFPGALoader as above (or the Gowin IDE steps). Check the pin TODOs in `tangnano20k.cst` first.
2. `python -m pip install -r hw\board\requirements.txt` (numpy, pyserial; numba makes dry runs fast).
3. Dry run (no board): `python cortex_host.py --dry-run --per-class 300 --data D:\cortex_data`
   expected (SIMULATED): stage 5 about 0.91 on all 10 digits, and "emulator matches the integer chip model exactly: True".
4. Real board, quick: `python cortex_host.py --port COM5 --per-class 300 --data D:\cortex_data` (COM port from Device
   Manager; the UART is usually the second BL616 port). The board should print the same accuracies as the dry run,
   because the core is bit-exact with the emulator. Any difference means a hardware or link problem.
5. Full run: drop `--per-class`. Dreams travel in batches of up to 256 per message, so the serial link is no longer
   the main cost; the time is mostly the chip dreaming (~1 ms per dream).
6. Let the chip see for itself: add `--onchip-encode`; the PC then sends the detectors once and raw images after that.
   Results must be identical to step 4 (the encoder is bit-exact with the PC's).

LEDs: led0 toggles per command, led1 core busy, led2 the last example or dream changed the table (surprise), led3
heartbeat, led4 UART activity, led5 last prediction was a class 0-4.

## Memory transfer demo: `cortex_transfer.py` (one board is enough)

The chip learns digits 0-4 and its memory is saved to a file; it is wiped, learns 5-9, saved again; the PC merges the two
memories (tables added, dream counts added) and loads the result; one self-regulated night; test on all ten digits.
`python cortex_transfer.py --port COM5 --per-class 300 --data D:\cortex_data` (or `--dry-run`; add `--handover` to load the 0-4 memory and learn 5-9 on top instead of merging, see [merge vs hand-over](../brain/experiments/month4/merge_variants.md)). Export or import of
the whole memory takes about 10 s at 115,200 baud. The saved `.npz` files can be loaded into another board.
Dry run (SIMULATED, emulator bit-exact with the chip): 0-4 alone 51.2% on all ten digits, 5-9 alone 42.4%, merged
78.9% before sleep, **91.4% after one night of 256 dreams**. The memory commands are bit-exact over UART
(`check_cortex_board.py`: 131 commands, 333 reply bytes, 0 mismatches).

## Power and speed benchmark: `cortex_bench.py`

Fixed 30 s phases (idle, link only, decide, learn, dream); type the USB meter reading after each. Energy per operation
above the link cost = (P_phase - P_link) / operations per second. Plan and caveats: `docs/month4_board_plan.md`.

## Live demo for the pitch: `cortex_demo.py`

A window where you draw with the mouse and teach the chip (tkinter, ships with Python on Windows; numpy needed).
`python cortex_demo.py --preload 200 --classes 0-7 --data D:\cortex_data` (emulator) or add `--port COM5` (board).
The chip starts knowing digits 0-7. Draw a new symbol, type a free class (8 or 9), press Teach 5-10 times, press
Sleep, then Test old digits.
Headless check of the same steps (emulator, SIMULATED): preloaded 0-7 at 93% on real test digits; taught class 8 from
10 examples in 0.1 s; after a 3,000-dream sleep, 73.5% on 200 real test 8s and 90.0% on old + new digits together.

## Sound demo

`python hw/board/cortex_sound_demo.py --data D:\\cortex_data [--port COMx]`: say a new word a few times and teach it
(needs Speech Commands and scipy; microphone needs `pip install sounddevice`). New words need many repetitions:
[numbers](../brain/experiments/month4/sound_on_board.md).

## Board day in one command

`python hw/board/board_day.py --port COMx --data D:\\cortex_data [--sound]` runs the plan's steps 0-5 (and 9) in order
and saves all output in one report file to send back.

## Before a board session

`python hw/board/preflight.py --data D:\cortex_data [--port COMx]` checks Python, packages, data, the bitstream and the
serial link (ping), and says what to fix.
