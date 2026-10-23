---
title: Tang Nano 20K preparation of the L tile (23 Oct 2026)
tags: [l, fpga, board, results]
---

# Single-tile board build, ready for the Tang Nano 20K (SIMULATED + synthesis; NOT yet run on a board)

- **Design:** `hw/rtl/tile/tile_board_top.v`: one L tile (router + bank + controller) behind the existing UART blocks (same pins as `lookup_board_top`, `hw/board/tangnano20k.cst` unchanged; pin names still carry the TODO note to be checked against the Sipeed schematic). Protocol: `E` ping (reply 5A); `T` + 9 flit bytes (reply: 9-byte response flit for a lookup, `K` for a posted update). Host script `hw/board/tile_host.py`.
- **Simulation (MEASURED in RTL simulation, iverilog):** `hw/rtl/tile/tb_tile_board.v` bit-bangs the UART at a fast baud: ping, one update, one lookup, reply checked byte for byte: **TILE BOARD PASS**.
- **Synthesis (yosys `synth_gowin`, `hw/asic/tile/synth_gowin.ys`, AW=15 = 32,768 x 16 bit = 64 KB):** 1,014 cells in total: 115 ALU, 569 flip-flops, about 280 LUTs, **32 block-RAM primitives (DPB)**; the GW2AR-18 has 46 block RAMs, so 64 KB fits. Statistics in `synth_gowin_stat.txt`; netlist `tile_board_gowin.json`.
- **Not done:** place and route and the bitstream (no nextpnr-gowin / Gowin tools in this container), so no timing or clock-rate result and nothing measured on hardware.
- **Power logging:** `hw/board/esp32_ina219_logger/` (existing sketch) measures board current; run the host script in a loop with the logger running to get energy per lookup. Board numbers will be FPGA numbers, not chip numbers.
- **To do on the day the board arrives:** install Gowin tools or the open flow (yosys + nextpnr-himbaechel + apicula), build, load, run `tile_host.py`, then the logger.

Related: [Results index](INDEX.md), [Hardware index](../HARDWARE_INDEX.md), [Board README](../board/README.md), [Journal](../../docs/journal.md)
