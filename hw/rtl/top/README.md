---
title: L chip top (dispatcher over the layers), RTL check
tags: [spark, rtl, dispatcher, hardware]
---

# L chip top (hw/rtl/top)

`l_chip_top.v` puts the layers behind one command interface: op 0 recognises an image (L Cortex stage 1, with L Deep woken only when the margin is at most the routing threshold), op 1 runs a numeric job on L Forge (a matrix product). The outputs `cortex_active`, `deep_active` and `forge_active` show which layer is awake; a power controller would use them to gate clocks and memory banks (the gating itself is not built). Check: `python hw/rtl/top/run_check_top.py` (copies the hex files into a temporary folder): **28 Oct 2026, 40 recognitions (6 routed at the recommended 20% routing; 13 with the older 30%) and one 16 x 128 x 16 matrix product, 0 mismatches against the golden models; cycles awake in that run: Cortex stage 184,760, Deep 222,970, Forge 2,051** (of about 1.23 million simulated cycles, including loading the input bits).

Related: [Hardware index](../../HARDWARE_INDEX.md), [L Deep build](../../results/l_deep_build.md), [Forge lane and traffic](../../results/forge_lane_and_traffic.md)
