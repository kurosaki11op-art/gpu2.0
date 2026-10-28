---
title: L Deep RTL (routed clause layer), bit-exact against the integer golden model
tags: [spark, rtl, l-deep, hardware]
---

# L Deep core (hw/rtl/deep)

`ldeep_core.v` is stage 2 of the L pipeline for one routed image: it adds the stage-2 table rows of the active code bits, evaluates the 4,000 kept clauses literal by literal with early exit, adds the table row of each clause that fires, and takes the argmax (first maximum wins). Integer only: adds and compares, no multiplier. Input: L's 4,608 code bits followed by 1,568 raw pixel bits (> 85 and > 170).

- Golden model and exporter: `hw/brain/experiments/month5/ldeep_golden.py` (rebuilds the best simulated configuration from the saved clause state, writes the `deep_*.hex` memories, 300 routed test images and the expected scores).
- Check: `python hw/rtl/deep/run_check_deep.py` (iverilog; 300 routed images, 10 scores and the prediction compared exactly). **28 Oct 2026: 0 mismatches over 300 images, mean 20,540 cycles per routed image (min 17,203, max 22,926).** Never run two RTL checks in the same folder at once (they share `out_deep.txt`).
- `ldeep_core_bram.v` (block-RAM friendly, serial bit load, 62,341 cycles per routed image, check `python run_check_deep.py --bram`) and `l_system.v` (two stages plus dispatcher; check `python run_check_system.py`: 200 images, 58 routed, 0 mismatches, mean 22,814 cycles) are bit-exact against the same golden pipeline. Gowin synthesis counts: [L Deep build](../../results/l_deep_build.md).
- `ldeep_core_p.v` (four parallel engines; first run `python partition_engines.py 4`; check `python run_check_deep.py --parallel`): bit-exact, 16,066 cycles per routed image.
- Memories load from the hex files at time zero (simulation only); a board top would stream them from SRAM or flash.

Related: [Hardware index](../../HARDWARE_INDEX.md), [L Deep build](../../results/l_deep_build.md)
