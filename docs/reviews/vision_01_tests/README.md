---
title: Vision review 01 - test files
tags: [spark, review, tests]
---

# Test files for Vision review 01

Minimal tests of specific findings; nothing here changes project results. Run from the repository root with `new_start/experiments/step5_worst_case_model.rs` as input.

- [`patch_s5.py`](patch_s5.py): makes a patched copy of the step 5 model. `python patch_s5.py IN.rs OUT.rs [--oldfab]`, then `rustc -O OUT.rs`. Base settings: `MM2GB=420 SRAM_PJ=0.55 GPU_PRICE_ABS=3320`. Switches: `V_ATTPJ`, `V_PUEG`, `V_PUEL`, `V_HBM`, `V_MACX`, `V_LOGICW`, `V_IDLE`, `V_PEAK`, `V_ADD`. `--oldfab` reverts the single-chip correction.
- [`q.py`](q.py): next-character loss by weight width (finding V-11). Needs a copy of `gpu_sim.rs` built as `gpu_sim_q` beside the work folder, with the weight limit 127 read from `V_WQ` in the weight loader and, when `V_QEMB` is set, `GATHER` quantising each table column to the same limit.
- [`k_check.py`](k_check.py): rebuilds the row K codes, reruns the recipe on 3 seeds and tracks a plain network per epoch (finding V-13). Data folder set inside the script.

Related: [Vision review 01](../vision_review_01.md), [Reviews index](../README.md)
