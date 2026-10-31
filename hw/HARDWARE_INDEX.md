---
title: Hardware index
tags: [spark, index, hardware]
---

# Hardware index

- [L core v0 RTL](README.md): the original spiking-style core, simulation and synthesis (Phase A).
- [Tang Nano 20K board](board/README.md): bring-up, power measurement, lookup-core UART protocol.
- [SKY130 ASIC flow](asic/README.md): open-source chip flow, gate-level verification (no fabrication planned yet).
- [FPGA floorplan](floorplan/README.md): placement on the GW2AR-18.
- [Power-measurement PCB](pcb/README.md): KiCad board for measuring L's power.
- [Chip evaluation PCB](pcb_chip/README.md): KiCad board for the ASIC.
- [Brain code (L Cortex)](brain/README.md): the current design's simulator and integer chip model.
- All checks at once: `sh hw/run_all_checks.sh DATA_DIR [--asic]` -> `hw/check_summary.txt` (41 checks, 22 Oct, one fresh full run, with the tail-memory, cue-weighting, second-look and threshold-unit checks: all PASS, none skipped, one uninterrupted run; keep the session active while it runs, the container is reclaimed when idle).
- L Cortex RTL: `rtl/cortex/cortex_core.v` (core), `board/cortex_board_top.v` (Tang Nano UART top); checks `rtl/cortex/run_check_cortex.py`, `board/check_cortex_board.py`. Sensory encoder `rtl/cortex/cortex_encoder.v` (check `run_check_encoder.py`); with `ENC_LEARN` it learns its own detectors (check `run_check_encoder_learn.py`). Core with `CORTEX_CONTEXT`: context memory (check `run_check_cortex_ctx.py`). Streaming cochlea `rtl/cortex/cortex_cochlea_stream.v` (live input, `run_check_cochlea.py --stream`). Cochlea `rtl/cortex/cortex_cochlea.v` (raw sound -> 28x28 sound picture, shift-add resonators; check `run_check_cochlea.py`, coefficients from `gen_cochlea_coef.py`). General encoder `rtl/cortex/cortex_encoder_gen.v` (images and sound; check `run_check_encoder_gen.py`). Sound chip `rtl/cortex/cortex_sound_top.v` (raw sound -> cochlea -> encoder -> core; check `rtl/cortex/sound/run_check_sound_chain.py`).
- Two senses (20 Oct 2026): `rtl/cortex/cortex_sense_top.v` (retina + cochlea into one core), `rtl/cortex/cortex_neighbours.v` (sleep neighbours), core `rd_scores` port; checks `run_check_sense_top.py`, `run_check_neighbours.py`, `run_check_sleep_clean.py`, `run_check_cortex_twosense.py`; see [sensory node](results/sensory_node.md).
- [Training experiments](train/experiments/README.md): accuracy and brain-like learning experiments (Phase A).
- [L tile and mesh RTL](rtl/tile/README.md): router, tile with memory bank, 4 x 4 mesh testbench replaying real lookups; 260 cycles per token, 0 wrong replies (SIMULATED).
- [Tang Nano 20K tile build](results/tile_board_prep.md): UART board top for one tile, simulated and synthesised (not run on a board).
- [ESP32 test of the L decision](board/esp32_l_test/README.md): self-measuring sketch (logic, speed, power on one board) plus analysis script, end-to-end procedure; logic verified on a PC build (0 of 200 differ); board run still to be done by the user.
- [Gate-level checks](synth/gate_level/sky130/README.md): core netlists (generic gates, SKY130 cells with macro models) against the integer model.
- [Layout checks 22 Oct](asic/cortex/signoff/README.md): routing, GDSII, timing, DRC of the L Cortex layout (DRC and hold fail).
- [L Deep RTL](rtl/deep/README.md): routed clause layer, bit-exact against the integer golden model (300 routed images, 0 mismatches, 28 Oct 2026).
- [L Forge RTL](rtl/forge/README.md): the block floating-point multiply-accumulate lane, bit-exact against the integer golden model (3,288 ops, 0 mismatches, 28 Oct 2026).
- [L chip top](rtl/top/README.md): dispatcher over Cortex, Deep and Forge with activity flags; 40 recognitions and a matrix product, 0 mismatches (28 Oct 2026).
- [Virtual FPGA device and tests](virtual/README.md): VFPGA-L1, the full regression, stress tests and the 3D board (28 Oct 2026).
- [Our GPU folder (hw/gpu)](gpu/README.md): [instruction set, programming model and functional simulator, M1](gpu/ISA_M1.md) and [M1 result](gpu/M1_result.md): CNN and transformer match PyTorch, INT8 agreement 99.4-99.9% (weight-only), W8A8 transformer 98.7% (31 Oct 2026)
- [L Forge tile mesh](rtl/mesh/README.md): routers and a distributed matrix product on 4 to 64 tiles, bit-exact against the lane golden model (28 Oct 2026).
- [FPGA bring-up kit](board/fpga_bringup/README.md): files and constraint template for the chosen board (pins left blank until the board is chosen and bought).
- [MCU port and ESP32 measurement](mcu/README.md): the L algorithm and a reference CNN in portable C, the ESP32 sketch and the USB-meter procedure.
- [Results index](results/INDEX.md): every result.

Related: [Home](../README.md)
