---
title: Error transport without multiplies through a gate network (first test)
tags: [l, accelerator, error-transport, gate-network, backprop-free]
---

# Can a gate network learn with a multiply-free error signal? First test (24 Oct 2026)

Direction (founder, 24 Oct): the chip must learn on its own, so the learning rule must use only lookups, adds, compares and counters. This is the first test. SIMULATED on CPU, MNIST digits, one seed, 3 gate layers (500, 500, 1,000 gates, fixed random wiring, 16 truth tables per gate, output = popcount of 10 groups of 100). Script: [bool_backprop.py](../brain/experiments/month5/bool_backprop.py); logs: [float and sign arms](../brain/experiments/month5/bool_backprop_float_signgrad.log), [integer arm](../brain/experiments/month5/bool_backprop_integer.log), [first integer attempt](../brain/experiments/month5/bool_backprop_integer_marginout_FAILED.log).

| Arm | What the error is | Test accuracy (hard gates) |
|---|---|---|
| float backprop (yardstick, not the design) | real numbers | 81.6% (6 epochs) |
| sign of the error, every layer | -1 / +1 | 20% |
| sign of the error, hidden layers only (output keeps its size) | -1 / +1 | 47% |
| ternary error on hidden layers (small errors become 0), threshold 1x mean | -1 / 0 / +1 | 68% at 3 epochs (still rising) |
| same, thresholds 2x / 3x / 5x (6 epochs) | -1 / 0 / +1 | 51% / 57% / 41% (noisy, not monotone) |
| ternary on every layer including the output | -1 / 0 / +1 | 9.8% (chance) |
| **integer-only rule** (hard gates, error = lookup of the Boolean derivative, 16 counters per gate) | -1 / 0 / +1 | **10 to 11% (failed)** |

## What the failures say
- **Magnitude matters at the output.** Sign-only at the output collapses (20%), keeping its size lifts it to 47%; a zero state in the hidden layers lifts it to 68%. A chip error signal therefore needs a small graded integer at the output (how wrong), and a zero ("leave alone") state inside.
- **Gap that remains: about 13 points** to float backprop for the best multiply-free error signal (68 against 81), one seed, thresholds noisy: TENTATIVE.
- **The fully integer rule (hard gates plus counters) does not learn.** Diagnosis: with random wiring and pass-through start, even the best possible choice of output-layer gates from full-data counts reaches only 23%, so the output layer cannot work without useful hidden features, while the hidden layers receive errors through gates that are still random. Float training avoids this chicken-and-egg problem with soft gates that move smoothly; hard gates with big counter jumps do not. Two attempted fixes (balanced one-vs-rest output targets, counters with no saturation) did not help.
- Not tested yet: graded integer output error, soft integer gates (counters mapped to probabilities by lookup), learned wiring, more gates.

## Round 2: graded integer error and integer counter updates (24 Oct 2026, same network, 4 epochs, MEASURED/SIMULATED)

Log: [bool_backprop_graded.log](../brain/experiments/month5/bool_backprop_graded.log). The error handed back through each layer is rounded to a small integer, and each gate's 16 counters change by one step (add or subtract 1) per batch, with no real-valued optimiser state.

| Setting | Test accuracy |
|---|---|
| float backprop, Adam (yardstick) | 81.0 to 82.1 (seeds 0 to 2) |
| error in 3 levels (-3..3) on hidden layers, per-example scale | 64.3 |
| 4-bit error (-15..15), per-example scale | 73.4 |
| 4-bit error, one scale for the whole batch | 78.6 |
| **4-bit error, one batch scale, integer counter updates** | **82.2 / 81.1 / 81.4 (seeds 0 / 1 / 2)** |

Reading:
- Level with float backprop on three seeds: error transport through gate layers does not need real numbers, multiplies or a real-valued optimiser. What it needs: a **graded small integer** error (about 5 bits), a **single scale per batch** (a power of two on a chip), and **counters moved by sign steps**.
- Earlier collapses (sign-only, 3 levels) came from throwing away how wrong an example is; per-example max scaling did the same by treating confident and wrong examples alike (-5 points).
- **Limit of this test:** the forward pass during learning is still the real-valued soft mixture of 16 gates (it needs multiplies); only the error path and the update are integer. The hard-gate integer forward (earlier arm) still fails. The chip-legal learning forward is the open piece. Also open: Fashion-MNIST and Shirt, larger networks, forgetting.

Related: [Results index](INDEX.md), [Error transport design](../../docs/error_transport_design.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
