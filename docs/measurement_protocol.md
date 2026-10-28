---
title: Measurement protocol - turning the estimates into MEASURED numbers
tags: [spark, measurement, protocol, evidence]
---

# Measurement protocol (28 Oct 2026)

For the founder, to run when the hardware is at hand. Until these runs exist, every energy number in the repository is ESTIMATED or SIMULATED. Record each run in the journal with its label (MEASURED once it comes from a sensor on real hardware), the date, the machine and the settings.

## 1. GPU baseline (needs an NVIDIA GPU)

Script: [gpu_energy_baseline.py](../hw/brain/experiments/month5/gpu_energy_baseline.py), tested here on the CPU path only (the build container has no GPU, so the GPU power code is untested).

1. `pip install torch pynvml` (a CUDA build of torch), then `python hw/brain/experiments/month5/gpu_energy_baseline.py DATA_DIR --epochs 10 --seconds 10` where DATA_DIR is the folder with the four `fashion-*-ubyte.gz` files (the one the repo's checks use).
2. Close other programs that use the GPU; keep the machine plugged in; let the GPU idle for a minute first.
3. The script trains the reference CNN (32 filters 3 x 3, pool, linear; about 91% expected), measures idle power for 5 s, then for float32 and float16 at batch sizes 1, 64 and 1024 runs a timed loop while sampling the GPU power sensor, and prints images per second, mean power, net power (minus idle), and millijoules per image net and gross. It writes `gpu_energy_baseline.json`.
4. Repeat the whole run three times on different days or after a reboot; report the mean and the spread. Report both net and gross; state that the sensor covers the whole board.
5. Add the numbers to the [claims register](claims_register.md) as MEASURED (GPU sensor), with the GPU model and driver version. Compare per image with L's estimates (L alone 30 nJ, L plus Deep 49 nJ, both ESTIMATED): a GPU image at batch 1024 is typically tens of microjoules or more, which is a measured reference for a ratio.

## 2. The board power of L Cortex (existing Tang Nano 20K build)

Existing documents: [month 4 board plan](month4_board_plan.md) and the [board README](../hw/board/README.md); the ESP32 self-measuring test is in [esp32_l_test](../hw/board/esp32_l_test/README.md). Procedure: USB power meter (or the project's power board) between the supply and the board; record idle power with the bitstream loaded and no work; run a loop of recognitions at a known rate; energy per decision = (running power minus idle power) divided by decisions per second; repeat five times. Label MEASURED (FPGA board), and state that an FPGA draws far more than an ASIC would, so this is a measured upper bound on chip energy, not the chip's energy.

## 3. The three-layer FPGA build (needs a larger FPGA)

Resource budget from synthesis (yosys, Gowin family; see [L Deep build](../hw/results/l_deep_build.md) and [Forge lane and traffic](../hw/results/forge_lane_and_traffic.md)): the L Deep two-stage system about 3,000 LUT4 and about 1.1 to 1.5 Mbit of block RAM; the Forge first tile about 3,000 LUT4, 16 multiplier blocks and a few block RAMs; four Deep engines about 3,500 LUT4. The whole board top (UART, dispatcher, Cortex-style stage 1, Deep with one engine, one Forge tile) synthesises to about 4,600 LUT4, 72 block-RAM blocks (about 1.3 Mbit) and 16 multiplier blocks; a device with at least about 10,000 LUTs, 1.5 to 2 Mbit of block RAM and 20 or more multiplier blocks leaves room (and the four-engine Deep core) (the Tang Nano 20K has 0.83 Mbit and is not). Candidate families to check against their data sheets and prices (recalled, not verified): Xilinx Artix-7 35T class (about 1.8 Mbit), Gowin GW5A class boards, Lattice ECP5-45 class. Needs: a UART or SPI loader for the memories and the input bits, a wrapper top for the board, and the vendor toolchain for that family. Measure as in section 2; compare images per second and energy per image with the GPU baseline.

## 4. What each measurement unlocks

| measurement | unlocks the claim |
|---|---|
| GPU sensor energy per image | a measured reference for the energy comparison |
| Cortex board power | the first MEASURED L number (an upper bound for the chip) |
| three-layer FPGA run | all three layers working together, on real hardware, with measured accuracy and cycles |
| layout of the Deep and Forge tiles | area and energy of the chip, replacing the assumed tile area |

Related: [Claims register](claims_register.md), [Status, 28 Oct 2026](L_status_28oct.md), [Docs index](INDEX.md), [Journal](journal.md)
