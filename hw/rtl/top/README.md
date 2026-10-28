---
title: L chip top (dispatcher over the layers), RTL check
tags: [spark, rtl, dispatcher, hardware]
---

# L chip top (hw/rtl/top)

`l_chip_top.v` puts the layers behind one command interface: op 0 recognises an image (L Cortex stage 1, with L Deep woken only when the margin is at most the routing threshold), op 1 runs a numeric job on L Forge (a matrix product). The outputs `cortex_active`, `deep_active` and `forge_active` show which layer is awake; a power controller would use them to gate clocks and memory banks (the gating itself is not built). Check: `python hw/rtl/top/run_check_top.py` (copies the hex files into a temporary folder): **28 Oct 2026, 40 recognitions (6 routed at the recommended 20% routing; 13 with the older 30%) and one 16 x 128 x 16 matrix product, 0 mismatches against the golden models; cycles awake in that run: Cortex stage 184,760, Deep 222,970, Forge 2,051** (of about 1.23 million simulated cycles, including loading the input bits).

`l_board_top.v` adds a UART front end (`uart_rx.v` and `uart_tx.v` from `hw/board`) so a PC can drive the layers: op 0x01 sends the 6,176 input bits and gets the routed flag, prediction and cycles back; op 0x02 runs the Forge matrix product and returns all 256 outputs. Check `python hw/rtl/top/run_check_board.py` (a UART model plays the PC; 2 non-routed and 2 routed images and the matrix product: **0 mismatches; reported cycles 4,619 and 4,619 for the not-routed images, 35,760 and 44,982 for the routed ones; matrix product 2,051 cycles**). Host script: [l_host.py](../../board/l_host.py) (protocol self-check passes; **not run on a board**). Gowin synthesis of the whole board top (yosys): about 4,600 LUT4 (4,595), 1,134 carry cells, about 780 flip-flops, 16 multiplier blocks and 72 block-RAM blocks (about 1.3 Mbit: the stage-1 and stage-2 tables, the clause memories and the Forge tile memories), so it needs a device with about 5,000 or more LUTs, more than 72 block-RAM blocks of 18 Kbit and 16 or more 9 x 9 multipliers; the Tang Nano 20K has 46 block-RAM blocks. No pin constraints are given because the board is not chosen.

Related: [Hardware index](../../HARDWARE_INDEX.md), [L Deep build](../../results/l_deep_build.md), [Forge lane and traffic](../../results/forge_lane_and_traffic.md)
