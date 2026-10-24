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

Related: [Results index](INDEX.md), [Error transport design](../../docs/error_transport_design.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
