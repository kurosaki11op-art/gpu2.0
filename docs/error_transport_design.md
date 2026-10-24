---
title: Error transport for L - design from our failures (24 Oct 2026)
tags: [l, design, error-transport, learning, failures]
---

# Blame-routed detector learning: a new error-transport technique for L, designed from our failures

**Standing method (user rule, 24 Oct 2026):** when no reliable technique exists for something we need, study how each attempt failed (win-lose or lose-lose), find the mechanism behind the failure, and invent the missing piece; only win-win changes are adopted, and a gain with a cost sends us back to find and remove the cause of the cost.

## 1. The problem

L's detector layer is learned without labels and then frozen; only the counting table sees errors. So (a) a new class must be written in features made for old ones (new-class recall 66% against 91% for a CNN with replay at 100 examples), (b) the features cannot learn what separates Shirt from T-shirt, Pullover and Coat (Shirt average precision 0.75 against 0.84, cluster accuracy 80.6% against 85.1%). A CNN passes the error back through every layer with backprop, which needs dense transposed matrices and multiplies (against the rules) and brings forgetting.

## 2. What our failures say

| Attempt | Outcome | Lesson |
|---|---|---|
| Direct feedback alignment on a hidden layer (month 4) | 83.9 against 84.8 baseline | random feedback carries no usable blame |
| Reward-gated detectors (memory file) | failed | a reward alone does not say which detector to move which way |
| Plain detector recruitment (24 Oct) | new-class recall +5 to +10, old-class accuracy -2.4 to -3.8: win-lose | new detectors overlapped the old code and fired on old images |
| Fine-tuning a CNN on the new class alone | forgets (old 90 to 3 percent) | any shared feature that moves for the new class can break the old ones |
| Float readout on the same bits | same accuracy | the table rule is fine; the evidence in the bits is the limit |

## 3. The technique (all integer, add/compare only)

1. **The blame is already in the table.** For a linear readout, the effect of an active bit b on "wrong class w instead of true class c" is d(b) = S[w, b] - S[c, b]: two table rows, sparse (only active bits), integer. This is the exact error signal the table's own update uses, routed one step further back.
2. **Route it to the detector that produced the bit.** Each active bit is (spatial cell, winning detector). If d(b) > 0 the detector's firing helped the wrong class: move its template AWAY from the patch (decrement the counters that agree with the patch); if d(b) < 0 it helped the true class: move it TOWARD the patch (the usual Hebbian step). Steps are the sign-only plus or minus one counter steps already used by the Hebbian fit; only the K most blamed bits per mistake per sign are used.
3. **Protect the old classes (win-win guard).** (a) importance gating: a detector that the old classes rely on (large table-row magnitudes on its bits) moves with small probability; (b) acceptance test: after a round the stored check set (held-out images, or a replay buffer) is re-encoded and the table retrained; the round is KEPT only if overall accuracy and cluster accuracy do not fall, otherwise reverted (cheap: a few hundred stored images).
4. **Recruit rather than rewrite when the code cannot express the new thing:** new detectors are fitted only on patches the old detectors explain badly and may fire only where they beat the old ones (novelty-gated recruitment, `newclass_gated.py`), so old bits stay valid.

## 4. How it is tested and what counts as success

`hw/brain/experiments/month5/blame_detectors.py`: rounds of blame updates on a 20,000-image subset with the acceptance test on 5,000 held-out images; baseline = same table with unsupervised detectors. **Success (win-win): test accuracy, four-class cluster accuracy and Shirt average precision all up, nothing else down.** Anything else is recorded as a failure and the failure analysed for the next design.

Related: [Docs index](INDEX.md), [Failure analysis](failure_analysis_clothing.md), [Claims ledger](claims_ledger.md), [Error transport paper notes](research/papers_notes/INDEX.md), [Journal](journal.md)
