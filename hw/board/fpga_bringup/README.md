---
title: FPGA bring-up kit for the three-layer design (pins to be filled from the chosen board)
tags: [spark, fpga, bringup, hardware]
---

# FPGA bring-up (hw/board/fpga_bringup)

The chosen board and checks are in the [FPGA board decision](../../../docs/fpga_board_decision.md). **No pin numbers are given here: I found none for the board and did not guess.** Fill the template from the board's schematic or example project.

Files to bring into the vendor project: `hw/rtl/top/l_board_top.v`, `hw/rtl/top/l_chip_top.v`, `hw/rtl/deep/l_system.v`, `hw/rtl/forge/forge_lane.v`, `hw/rtl/forge/forge_tile_mm.v`, `hw/board/uart_rx.v`, `hw/board/uart_tx.v`, and the memory initialisation files `hw/rtl/deep/deep_wcode1.hex`, `deep_wcode.hex`, `deep_wcl.hex`, `deep_hdr.hex`, `deep_lits.hex` and `hw/rtl/forge/mm_a.hex`, `mm_b.hex` (the tools read them through `$readmemh`; if the vendor flow needs another format, convert with a short script). Set the module parameters `CLK_HZ` (board clock) and `BAUD` (115200) of `l_board_top`.

Constraint template (names only; the location column is to be filled):

| signal | direction | board location |
|---|---|---|
| clk | input | (the board's oscillator pin) |
| rst | input | (a push button, active level to check) |
| rx | input | (UART receive pin to the USB-serial chip) |
| tx | output | (UART transmit pin) |
| led_deep, led_forge | output | (two user LEDs, optional) |

Related: [FPGA board decision](../../../docs/fpga_board_decision.md), [L chip top](../../rtl/top/README.md), [Hardware index](../../HARDWARE_INDEX.md)
