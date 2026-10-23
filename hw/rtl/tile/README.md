---
title: L tile and mesh (RTL, first version)
tags: [l, tile, mesh, rtl]
---

# L tile and 2-D mesh (RTL, 23 Oct 2026, SIMULATED)

First RTL of the wafer / multi-chip idea: a mesh of tiles, each with a bank of table memory and a bank controller, joined by two networks (request and response, XY routing, one flit at a time per link, ready/valid).

- `l_router.v`: 5-port mesh router (local, N, E, S, W), XY routing, input and output registers, rotating priority.
- `l_tile.v`: two routers + one memory bank of 16-bit words (two 8-bit counters) + bank controller: **lookup** (returns the word) and **posted update** (adds to both counters, saturating at 255, in place). The memory is a behavioural model; in the chip it becomes a wrapper around an SRAM macro with the same ports.
- `tb_mesh.v`: 4 x 4 mesh. Clients replay real counting-language-model lookups from `trace.hex` (3,200 tokens of real text, 48 lookups per token: 8 sequential steps of 6 parallel lookups; owner tile = slot mod 16). Every reply is checked against the owning memory's content.
- Run: `iverilog -g2012 -o mesh.vvp -Ptb_mesh.ACTIVE=1 -Ptb_mesh.NTOK=100 l_router.v l_tile.v tb_mesh.v && vvp -n mesh.vvp` (ACTIVE = number of client tiles running streams).

**Result (cycle-accurate RTL simulation, 100 tokens per stream):** one stream: 4,800 lookups, **0 wrong replies**, **260 cycles per token** (about 32 cycles per step). Sixteen streams at once (one per tile): 76,800 lookups, 0 wrong replies, **262 cycles per token per stream**, so 16 times the throughput for no latency cost at this load. At an assumed 500 MHz clock that is about 0.52 us per token per stream; this replaces the 200 ns link assumption in the earlier multi-chip estimate (which gave 1.64 us).

**Not yet:** hot-row copies, hardware sequencing of the token steps, link serialisation between chips, synthesis, placement of SRAM macros, power. Next: `sram_wrap` for the OpenRAM macro and synthesis of one tile.

Related: [RTL index](../../HARDWARE_INDEX.md), [Multi-chip results](../../results/multichip_lm.md), [Wafer design study](../../../docs/L_wafer_design.md)
