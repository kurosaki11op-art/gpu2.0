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

Related: [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Append-only clause banks](append_only_clause_staged.md), [Results index](INDEX.md)
