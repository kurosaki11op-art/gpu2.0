---
title: Knockout screen (gene-editing test) on L's detectors
tags: [l, detectors, knockout, clothing]
---

# Knockout screen: can we find "faulty" detectors and repair them? (24 Oct 2026)

Idea (user): like gene editing, keep the good detectors and repair the faulty ones. Test: mask the bits of one detector (128 detectors, 4 channels x 32), re-measure with the table fixed, on check set A and an independent check set B. Script and log: [knockout.py](../brain/experiments/month5/knockout.py), [knockout.log](../brain/experiments/month5/knockout.log). All numbers MEASURED (SIMULATED chip model), one seed.

| Finding | Value |
|---|---|
| Base accuracy / Shirt AP, check A | 0.8912 / 0.757 |
| Base accuracy / Shirt AP, check B | 0.8907 / 0.758 |
| Removal effect, A vs B, correlation | 0.42 (accuracy), 0.65 (AP) |
| Classes of detector | essential 2, neutral 94, "faulty" 32 (of 128) |
| "Faulty" confirmed on B | 5 of 32 |
| Mean removal effect on B | faulty -0.0004, neutral -0.0005, essential -0.0049 |

Retrained after removal (TEST, read once):

| Variant | Bits | Accuracy | Shirt AP |
|---|---|---|---|
| keep all | 4,608 | 0.8802 | 0.716 |
| drop the 32 "faulty" | 3,456 | 0.8795 | 0.716 |
| drop faulty + near-neutral | 1,440 | 0.8667 | 0.684 |

## Reading
- Almost no detector is reliably harmful: the "faulty" label mostly does not survive a second check set (5 of 32). Repairing them has nothing to gain; **the code is redundant, not faulty**.
- Win: a quarter of the detectors (1,152 bits) can be dropped with no change in accuracy or Shirt AP: 25% less table memory and bytes read (a win-win, but one seed, TENTATIVE).
- Dropping more costs real accuracy (-1.4 points at 1,440 bits), so the tail is not free.
- Shirt is not helped by any detector edit; the limit stays the single layer.

Related: [Results index](INDEX.md), [Claims ledger](../../docs/claims_ledger.md), [Journal](../../docs/journal.md)
