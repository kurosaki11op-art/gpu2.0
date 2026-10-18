---
title: "SPARK Cortex: a brain-principled chip that keeps learning after it ships"
date: 2026-10-18
tags: [paper, cortex, pitch]
---
# SPARK Cortex: a brain-principled chip that keeps learning after it ships

L Lawliet (Navin, CKCET). Short paper for the 23 October event. Labels: SIMULATED = our exact integer chip model or RTL simulation; ESTIMATED = layout tools or arithmetic on stated assumptions; **nothing is MEASURED on hardware yet**.

## Abstract

Neural networks forget earlier classes when they learn new ones, so a deployed network is retrained from scratch, which costs energy and hardware. We present SPARK Cortex, a small chip design that follows brain principles: sparse senses that learn without labels, one-pass learning by counting into a 5-bit table, sleep in which old classes are replayed from 10-bit counters instead of stored examples, and knowledge transfer between chips by adding counters. It uses no multiplier, no matrix product and no backpropagation. In the exact integer model, after five stages of new classes it keeps 95.8% (digits), 78.3% (clothing) and 82.9% (spoken words), where a network that fine-tunes at each stage keeps 19.5%, 20.0% and 15.9%. Learning everything at once, an optional slow second table (an ASIC build option) lifts it level with a small network: digits 98.4 vs 97.8, clothing 88.3 vs 87.3, words 87.5 vs 85.5 (5 seeds, SIMULATED); in stages clothing rises from 78.4 to 81.6; without it clothing trails by 2.5 points. The RTL is bit-exact with the model (21 checks), the base design fits a $25 FPGA in place and route, and a SKY130 layout estimate ends at one remaining routing violation.

## 1. Problem

A network trained in stages overwrites earlier knowledge. Replay of stored examples reaches only 49.6 / 37.8 / 27.8% with 20 images per class in our test, and retraining from scratch costs energy, heat and discarded hardware.

## 2. Design

1. **Senses.** Receptive-field detectors with winner-take-all and Hebbian counters (XNOR plus popcount); for sound a streaming cochlea, a noise floor and word alignment (every word start shifted to the same frame).
2. **Learning.** Each example is counted into a table (5-bit entries, margin rule 32); no gradient.
3. **Sleep.** Per class, 10-bit counters generate dreams by rejection sampling; the night ends by itself when fewer than a threshold of surprises remain.
4. **Few-shot after shipping.** IMPRINT: a novel example raises its class row immediately; a short sleep (300 dreams per known class) blends it in.
5. **Sharing.** Memories merge by adding counters, or one chip hands its memory to another.
6. **Slow table (option).** A second 8-bit table follows the fast table by slow shift-and-add averaging (time constant 16,000 ticks) and is the one used to decide; it removes the order noise of one-pass learning and damps the bias toward the newest classes (consolidation lag).

## 3. Results (SIMULATED, exact integer model)

| Test | Digits | Clothing | Words |
|---|---|---|---|
| 5 stages, chip | 95.8 | 78.3 | 82.9 |
| 5 stages, fine-tuned network | 19.5 | 20.0 | 15.9 |
| All at once, chip (today) | 98.0 | 84.8 | 84.7 |
| All at once, chip with the slow table (ASIC option) | 98.4 | 88.3 | 87.5 |
| 5 stages, chip with the slow table (K = 5) | 95.9 | 81.4 | 83.6 |
| All at once, network (MLP) | 97.8 | 87.3 | 85.5 |
| 1 example per new class (all 10 classes), IMPRINT | 69.9 (was 54.1) | 64.0 (was 49.7) | 48.3 (was 45.2) |
| Merge two chips / hand-over | 93.3 / 95.6 | 81.4 / 82.7 | 64.3 / 71.6 |

Sound in noise (trained clean): 80.3 / 72.4 / 58.9 / 47.1% at clean / 20 / 10 / 5 dB. Word alignment raised sound from 71.9 to 82.5% all at once.

## 4. Cost (design fact, SIMULATED, ESTIMATED)

84 KB for images (137x less than our first version), 422 KB for sound. Tang Nano 20K: 89% logic, 46/46 block RAM, 0 multipliers, timing met (SIMULATED place and route). Energy per decision about 74x below an 8-bit network counting operations needed (9.4 vs 696 nJ, ESTIMATED); SKY130 layout estimate 0.18 to 0.26 uJ per decision. Logic under 1 mm2, 18.8 mm2 with open SRAM macros (ESTIMATED).

## 5. Limits and failures

Without the slow table clothing trails the network by 2.5 points all at once; with it the chip is level, not better (a floating-point MLP on raw clothing pixels reached 88.4, a small CNN 89.2, a CNN on words 91.4). Staged clothing is 81.4% with the slow table (78.3% without; multi-prototype dreams add up to +0.7 more); the finer detector grid raises all-at-once accuracy a little but made staged digits worse in an earlier test. The remaining limit in stages is dream fidelity. New spoken words from 1 to 5 recordings reach only 12 to 29%. Rejected ideas include a second sensory layer, expansion coding, onset channels, tempo and pitch normalisation, wider sound detectors, a shared prototype pool, table rebuilds and merge variants (see [journal](journal.md) and [what limits the scores](../hw/brain/experiments/month4/slow_table_and_staged_limits.md)). A new condition of known classes (rotated digits) cut upright digits from 95 to 45% without a frozen dream memory (85% with it, an ASIC build option). Nothing is measured on hardware; data are small standard image sets and a 10-word speech set.

## 6. Related work

Hyperdimensional-computing accelerators and Intel Loihi 2 also learn continually ([prior art](prior_art_cortex.md)). After 5 stages we are ahead of an HDC baseline on digits by 2.2 and on sound by 5.7 points in our own test (SIMULATED).

## 7. Conclusion

A multiplier-free chip can keep learning after deployment, keep what it knew and move knowledge between chips; it is weaker than a network in specific, stated places. Next: the real board run (first MEASURED numbers), then learned word features and higher-fidelity dreams.

Related: [Pitch script](pitch_script_cortex.md), [Q&A sheet](pitch_qa_sheet.md), [Claims sheet](cortex_claims_sheet.md), [Results at a glance](results_at_a_glance.md), [Project memory](PROJECT_MEMORY.md)
