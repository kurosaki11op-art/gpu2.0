---
title: L Forge RTL (block floating-point lane), bit-exact against the integer golden model
tags: [spark, rtl, l-forge, hardware]
---

# L Forge lane (hw/rtl/forge)

`forge_lane.v` is the multiply-accumulate lane of the L Forge tile: one block of 16 signed 8-bit mantissa pairs with block exponents per cycle, exact integer dot product, added into a floating accumulator (16-bit mantissa magnitude, round to nearest, ties away from zero). Golden model and vector generator: `hw/brain/experiments/month5/forge_lane_golden.py`. Check: `iverilog -g2012 forge_lane_tb.v forge_lane.v` then `vvp` (run from this folder); **28 Oct 2026: 3,288 operations (including sequences with exponent gaps above 40 bits), 0 mismatches.** The vectorised emulation used by the tile model (`forge_tile_model.py`) matches the scalar golden model on 300 random sequences.

Related: [Hardware index](../../HARDWARE_INDEX.md), [Forge lane and traffic](../../results/forge_lane_and_traffic.md)
