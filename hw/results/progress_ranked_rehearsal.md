---
title: Progress-ranked rehearsal (the chip chooses what to rehearse)
tags: [spark, results, thinking, goals]
---

# Progress-ranked rehearsal (27 Oct 2026)

SIMULATED, Fashion-MNIST, 6 old + 4 new classes, one seed. Part 4 of the thinking plan. Script `hw/brain/experiments/month5/staged_progress.py`, logs `staged_progress_clean.log`, `staged_progress_sab.log` (first version), `staged_progress_clean_v2.log`, `staged_progress_sab_v2.log` (minimum 6 chunks). The controller of [the staged note](append_only_clause_staged.md) with the hand-set pair weights replaced by a drive built from signals the chip holds, with no labels: per-class doubt (share of probe images predicted as class c whose top-2 margin is small) is tracked per chunk, learning progress of class c is its drop in doubt, class sampling weights are 0.2 uniform floor plus 0.8 times a noisy normalised progress (Thompson-like), the night ends when progress stays near zero for 2 chunks (not before chunk 6 in version 2), every chunk prints a decision log (progress and weights). Set-points are read-only constants (1/10 per class, alarm threshold 0.05). The share-distance tripwire with undo is kept.

| run | final accuracy (old / new / Shirt) | notes |
|---|---|---|
| uniform schedule, 8 chunks (earlier) | 83.0 (82.5 / 83.7 / 0.47) | no controller |
| hand-set pair weights controller (earlier) | 82.3 to 83.0 | stopped itself after 5 to 7 chunks |
| progress-ranked, version 1 (could stop at chunk 3) | 81.6 (81.4 / 81.8 / 0.44) | stopped too early |
| progress-ranked, version 2, clean | **83.3** (82.8 / 84.0 / 0.52) | 3 false alarms undid chunks 3, 4, 5 |
| progress-ranked, version 2, chunk 3 corrupted (45% noise in rehearsal images) | 82.9 (82.4 / 83.5 / 0.50) | alarm raised the share distance by 0.23, chunk undone, recovered |

- **Parity with the uniform schedule and the hand-set controller (83.3 against 83.0), with no human-set schedule**: the chip chooses its own class weights and its own stopping point. Differences of 0.3 are inside the 1-point run-to-run spread, so this is parity, not a win; that is also what the research note set as the success criterion.
- **The tripwire works on a real fault** (corrupted chunk: share distance +0.23, undone, final 82.9) **but fires falsely on clean chunks** (increases of 0.05 to 0.07, threshold 0.05), wasting three chunks of work. The two kinds of event are separated by a wide margin (0.23 against 0.07), so a threshold near 0.12 should keep the real alarm and drop the false ones; not yet re-run.
- The progress weights are plausible (the confused upper-body classes get the largest weights, 4 to 5 times the floor) but their effect alone, against uniform weights under the same tripwire, is not isolated.

### Alarm threshold 0.12 (27 Oct 2026, `staged_progress_clean_v3.log`, `staged_progress_sab_v3.log`)

Raising the alarm threshold from 0.05 to 0.12 removed the false alarms on the clean run but did not give a better result: clean run 81.4 (stopped early, old 80.7, new 82.5, Shirt 0.57) and corrupted-chunk run 79.9 (the alarm fired one chunk late, at chunk 4 with a rise of 0.13, so the corrupted chunk 3 was kept). So the threshold is not a clean fix: the share-distance rise caused by a corrupted chunk varied from 0.13 to 0.23 across runs, overlapping the 0.05 to 0.07 false-alarm range at the low end. **Part 4 stands at parity at best (83.3 with threshold 0.05, 81.4 with 0.12, against 83.0 for uniform), with run-to-run differences of 1 to 2 points; the tripwire is real but its threshold is sensitive.** A rise measured over two chunks, or a threshold set from the chip's own recent chunk-to-chunk spread, is the next thing to try.

### Closing run: three alarm designs, two repeats each, against no controller (27 Oct 2026, SIMULATED)

Corrupted chunk moved to chunk 4 so a spread-based rule has history. Final accuracy (all ten classes), clean runs and corrupted-chunk runs; logs `staged_progress_{adapt,fix10,uniform}_sab{0,1}_{a,b}.log`.

| alarm design | clean a / b | corrupted a / b | what the alarm did |
|---|---|---|---|
| no controller (uniform schedule, 8 chunks) | 83.4 (one run) | 82.3 (one run) | nothing; the stream recovers from the bad chunk by itself |
| fixed threshold 0.05 (earlier) | 83.3 | 82.9 | 3 false alarms on the clean run |
| adaptive threshold max(0.04, 4 x median chunk-to-chunk change) | 82.6 / 83.8 | 82.8 / 82.2 | 2 false alarms in clean b, 1 in corrupted a; caught the corrupted chunk in both |
| fixed threshold 0.10 | 82.5 / 83.3 | 80.8 / 82.5 | no false alarms; missed the corrupted chunk in a (rise below 0.10), caught it in b (rise 0.18) |
| plus accuracy on the chip's stored images | | | 1.000 at every chunk (the stored images are trained on constantly): no signal; runs stopped |

- **No design is clearly better than no controller.** Every controller result (80.8 to 83.8) sits inside the spread of the uniform runs (82.3 to 83.4) plus the 1 to 2 point run-to-run noise. The earlier claim that the tripwire lifted a corrupted run from 81.4 to 83.0 was one run against one run and was inside that noise.
- **The share-distance rise does not separate a harmful chunk from a normal one reliably**: normal chunks raised it by 0.05 to 0.08 and a harmful chunk by 0.06 to 0.25 depending on how much damage the corrupted chunk did; any threshold trades false alarms against misses.
- A harm signal the chip can trust would need held-out evidence that is not trained on (for example dreams not used for training, or a held-out slice of the unlabeled probe scored against the old model's own answers); the stored images are useless for it. Not built.
- **Part 4 stands at parity**: the chip can pick its own class weights and its own stopping point with no human-set schedule and ends where the uniform schedule ends (82.5 to 83.8 against 82.3 to 83.4). The tripwire is a working mechanism but its benefit was not shown; keep it as a safety option, not a claim.

### Fix attempt: a harm signal that is not trained on (27 Oct 2026, `staged_progress_agree_sab{0,1}_{a,b}.log`)

New signal, label-free and never trained on: the chip keeps the stage-1 model's confident answers on the unlabeled probe (the 50% of probe images with the largest top-2 margin) and measures how often the current model still gives the same answer; an alarm fires when that agreement drops by more than 0.04 from its best. It is independent of the share-distance signal that could not separate harm from noise.

| run | alarm result | final accuracy |
|---|---|---|
| corrupted chunk, run a | caught the corrupted chunk (agreement 0.586 against best 0.666); also one false alarm on a clean chunk (drop 0.087) | 81.1 |
| corrupted chunk, run b | caught the corrupted chunk by agreement (drop 0.048) when the share-distance rise was only 0.048, which the 0.10 share threshold would have missed | 82.8 |
| clean runs a / b | no false alarm | 83.6 / 82.8 |

- Detection is better than with the share signal (2 of 2 corrupted chunks caught, 1 false alarm in 4 runs against misses and several false alarms before) but final accuracy is still inside the noise of the uniform runs (82.3 corrupted, 83.4 clean), and one corrupted run still dipped to 78.8 right after the fault. So the chip now notices harm reliably enough to act on, but a measurable accuracy benefit from acting is not shown at this run count.
- Open: a smaller undo (halve only the damaged classes), repeating until the benefit is visible, a larger fault set.

Related: [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Append-only clause banks](append_only_clause_staged.md), [Results index](INDEX.md)
