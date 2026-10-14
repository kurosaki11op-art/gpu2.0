---
title: Hardware index
tags: [spark, index, hardware]
---

# Hardware index

- [SPARK core v0 RTL](README.md): the original spiking-style core, simulation and synthesis (Phase A).
- [Tang Nano 20K board](board/README.md): bring-up, power measurement, lookup-core UART protocol.
- [SKY130 ASIC flow](asic/README.md): open-source chip flow, gate-level verification (no fabrication planned yet).
- [FPGA floorplan](floorplan/README.md): placement on the GW2AR-18.
- [Power-measurement PCB](pcb/README.md): KiCad board for measuring SPARK's power.
- [Chip evaluation PCB](pcb_chip/README.md): KiCad board for the ASIC.
- [Brain code (SPARK Cortex)](brain/README.md): the current design's simulator and integer chip model.
- SPARK Cortex RTL: `rtl/cortex/cortex_core.v` (core), `board/cortex_board_top.v` (Tang Nano UART top); checks `rtl/cortex/run_check_cortex.py`, `board/check_cortex_board.py`. Sensory encoder `rtl/cortex/cortex_encoder.v` (check `run_check_encoder.py`); with `ENC_LEARN` it learns its own detectors (check `run_check_encoder_learn.py`). Core with `CORTEX_CONTEXT`: context memory (check `run_check_cortex_ctx.py`).
- [Training experiments](train/experiments/README.md): accuracy and brain-like learning experiments (Phase A).
- [Results index](results/INDEX.md): every result.

Related: [Home](../README.md)
