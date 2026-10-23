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

## 23 Oct (later): SRAM wrapper, OpenRAM build and first synthesis of one tile (SIMULATED / synthesis)

- `sram_wrap.v`: memory-agnostic bank (one synchronous read port, one write port, 16-bit words, 2^AW words). Builds: behavioural (simulation), `-DOPENRAM` (the open SKY130 macro, two 16-bit words per 32-bit row, byte-masked write, 512-row banks, each port clock gated by its own select), or any other memory by replacing the module body.
- `l_tile.v` now has a bank controller (one request at a time: read, then respond or write back) and, in the OpenRAM build, a **zero-fill after reset** (the macros power up unknown): 4,096 cycles for AW = 12.
- Checks (`run_check_tile.sh`): 4 x 4 mesh with 16 streams, **38,400 lookups, 0 wrong replies, 268 cycles per token**; one tile with the four OpenRAM macros, **24 lookups checked, 0 mismatches** (even and odd word addresses, all four macro banks, accumulation, saturation at 255).
- **Synthesis of one tile** (SKY130 hd cells + 4 OpenRAM macros, AW = 12 = 8 KB, `hw/asic/tile/synth_tile.ys`, `synth_stat.txt`): 5,753 cells (1,404 flip-flops, 8 clock gates, 4 macros), total area 1.20 mm2 of which the macros are 1.14 mm2: **the logic (two routers, controller) is under 5% of the tile; memory is 95%**. Placement, clock tree, routing and power of the tile come next.

Related: [RTL index](../../HARDWARE_INDEX.md), [Multi-chip results](../../results/multichip_lm.md), [Wafer design study](../../../docs/L_wafer_design.md)
