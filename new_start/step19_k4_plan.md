---
title: Redesign test 4 - a learned prototype layer with a closed-form readout at full data: can L reach a tuned network on clothing? Pre-set bars (31 Oct 2026)
tags: [spark, new-start, redesign, accuracy, prototypes, readout, test-plan, bars]
---

# Redesign test 4: close the clothing gap (31 Oct 2026)

**Written before any run.** Founder (31 Oct 2026): if the current L fails against what GPU models do on clothing and everything, fix it or redesign it. State of the current design (all MEASURED): clothing 88.85% (89.73% with L Deep) against a tuned small network at 89.9% to 90.7% and a strong one at 91.75%; digits within 0.35 points of a tuned network ([test 2](step17_k2_result.md)); few labels mostly a readout weakness ([test 3](step18_k3_result.md)). The two findings that point to a redesign: **a ridge readout on the same code beat the shipped counting readout by 5 to 12 points at 100 to 300 labels, and prototypes learned without labels added 1 to 2.5 points more.** Question: at full data, does the same two-part design (a layer of prototypes learned without labels, then a closed-form readout) reach the accuracy of a tuned small network? Script: [`k4_prototype_layer.py`](experiments/k4/k4_prototype_layer.py). CPU, cloud container.

## Designs compared (the main one is fixed in advance)

- **R0** references: the shipped recipe (88.85% clothing, 98.60% digits, test 2).
- **R1** ridge regression on the 4,608-bit code, 60,000 labels.
- **R2** 1,000 prototypes (3 passes of k-means on the unlabelled code) + ridge.
- **R3 (MAIN)** 3,000 prototypes + ridge. Penalty chosen on a held-out tenth of the labels, then refitted on all labels; 2 clustering seeds, mean reported.

Each prototype similarity is an XNOR-and-bit-count dot product with the 4,608-bit code, the operation the chip's encoder already performs; the readout is a 3,000 x 10 table of weights (a small hybrid multiply-add block, allowed since the 31 Oct 2026 decision).

## Pre-set bars (judged on R3)

| id | bar |
|---|---|
| **K4-a** clothing | test accuracy at least 90.0% (the lower end of the tuned small network's measured 89.9% to 90.7%) |
| **K4-b** digits | test accuracy at least 98.9% (the tuned network's 98.95% minus 0.05) |
| **K4-c** inference cost | counted energy per image (similarities plus readout, raw constants, no layout factor on either side) at most the small network's forward pass (about 0.66 million 16-bit multiply-adds, 1.0 uJ) |
| **K4-d** training cost | counted total training energy (fixed encoder fit, 60,000 encodings, clustering, readout; L side x28) at most one fifth of the tuned network's at 60,000 labels (2.5 J counted in test 2) |
| **K4-e** chip realism | the readout quantised to 8-bit weights (per-class scale) loses at most 0.5 points against the float readout; 5-bit is reported |

All must pass for "the redesign reaches a tuned network on both tasks" to stand. A miss is reported as a miss; no bar changes after the run.

## Limits stated in advance

Host-trained float readout (quantisation tested, hardware not); counted, not measured, energy; two small image tasks; a strong network (91.75%) is not the target of this test; 3,000 prototypes and 3 passes are fixed choices; the prototype layer needs 3,000 x 4,608 bits of memory (1.7 MB) in addition to the existing tables.

Related: [Step 18 test 3 result](step18_k3_result.md), [Step 17 test 2 result](step17_k2_result.md), [Workload map](../docs/gpu_workload_map.md), [New start charter](README.md), [Docs index](../docs/INDEX.md)
