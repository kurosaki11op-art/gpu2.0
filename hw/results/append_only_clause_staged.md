---
title: Append-only clause banks with classes arriving in stages
tags: [spark, results, continual, clauses]
---

# Append-only clause banks with classes arriving in stages (26 Oct 2026)

SIMULATED, Fashion-MNIST, one seed, 300 clauses per class, clause literals = L's detector code + raw-pixel bits, scores = unclipped clause sums, class-incremental (no task label at test). Script `hw/brain/experiments/month5/tm_staged.py`, logs `tm_staged_none.log`, `tm_staged_dream.log`.

Stage 1 trains classes 0 to 5 jointly. Stage 2 trains only new banks for classes 6 to 9 from new-class images; the old banks are checked to be bit-for-bit unchanged (append-only; "old banks untouched: True" in both runs). No old image is kept. The dream variant draws negatives for the new banks from a stored table of per-class bit frequencies (6,176 counters per class).

| | all ten classes | old classes (0 to 5) | new classes (6 to 9) | Shirt recall |
|---|---|---|---|---|
| stage 1 alone (6 classes) | 90.1 (6 classes) | 90.1 | - | - |
| stage 2, no dreams | 58.3 | 64.3 | 49.2 | 0.667 |
| stage 2, frequency dreams | 72.6 | 83.5 | 56.1 | 0.410 |
| joint reference (same code, epochs 2 to 3, noisy) | 82.0 to 83.5 | 77 to 91 | 73 to 89 | up to 0.76 |

## What this says

- **Nothing is forgotten in storage, but accuracy still falls**: the old banks are intact, yet old-class accuracy drops from 90 to 64 (no dreams) because the new banks fire on old-class images they never saw as negatives. This is competition, not overwriting, the same finding as the earlier neurogenesis tests.
- **Dreams help a lot but do not close it**: frequency dreams as negatives lift old-class accuracy to 83.5 and the total to 72.6, still about 10 points below joint training, and new classes stay weak (56). The old banks cannot be told about the new classes without being modified, so new images fire old clauses (one-sided correction).
- **Not solved.** The remaining gap needs the old banks to learn that new-class images are not theirs without being rewritten, for example a small appended veto clause set per old class trained from new-class images (not tried), or the old-versus-new decision at the table.
- Caveats: the joint reference is unstable (accuracy swings between epochs with unclipped sums and T=25); only 3 epochs per stage; one seed.

## Veto clauses: the old classes learn the difference themselves (26 Oct, SIMULATED, one seed)

After the stage above, each old class gets an appended bank of 300 veto clauses (negative polarity, new memory; the original clauses are untouched). A veto learns "this is not mine" from new-class images and "this still is mine" from the old class's own dreams (stored bit frequencies). Script `tm_staged2.py` (MODE=veto), log `tm_staged_veto.log`. A first run (`tm_staged_veto_bug_run.log`) learned nothing because empty veto clauses did not fire during training (0 included literals, result equal to the dream baseline); fixed and rerun.

| After 3 veto epochs | all ten classes | old | new | Shirt recall |
|---|---|---|---|---|
| frequency dreams only (same stage 1) | 75.9 | 86.7 | 59.6 | 0.321 |
| + veto clauses | 80.3 | 76.5 | 86.0 | 0.673 |
| joint training (reference, unstable) | about 82 to 83.5 | | | |

- The gap to joint training falls from about 8 to about 3 points, with no old clause rewritten and no image kept. New classes recover (60 to 86); the old classes now lose some (87 to 76) because vetoes learned against crude dreams sometimes reject real old images. The dream is the weak part: independent bit frequencies are not what real images look like.
- Not yet done: choose which old classes to compare by confusion (vetoes are spread at random over old classes now), better dreams (dreams from the old clauses themselves), more veto epochs. Memory grows by the veto bank (here as large as the original bank; pruning not tried).

### Clause-based dreams and confusion-targeted vetoes (26 Oct, SIMULATED)

Dreams now start from the class bit frequencies and force the literals of a random positive clause of that class, kept only if the class's own clauses score it at 3 or more; 70% of veto updates compare against the nearest known class (the one that claims the new image most). Log `tm_staged_veto_d1t1.log`.

| | all ten | old | new | Shirt recall |
|---|---|---|---|---|
| veto, frequency dreams, random class | 80.3 | 76.5 | 86.0 | 0.673 |
| veto, clause dreams, targeted | 81.1 | 77.6 | 86.3 | 0.626 |

Only +0.8. Old classes stay at 77.6 against 90.8 before the new classes came. The overall gap to joint training is now about 1 to 2 points, but it is bought by the new classes (86) while the old classes pay (about 13 points). Cause not yet isolated: whether old test images are lost to the new banks (new clauses firing on them) or to the vetoes. Next: log where the old-class errors go, and train the new banks with clause-based dreams of the old classes as well.

### Where the old-class errors go (26 Oct, SIMULATED; logs `tm_staged_veto_diag.log`, script `staged_decide.py`)

Same recipe, another stage-2 draw (81.9 overall, old 80.6, new 84.0). Old-image errors:

| | old-image errors | to a new class | to another old class | new images lost to an old class |
|---|---|---|---|---|
| without vetoes | 13.9% | 7.4% | 6.5% | 39.4% |
| with vetoes | 19.4% | 14.6% | 4.8% | 13.4% |

- The vetoes buy the new classes (39% to 13% of their images lost) and pay with old images: they fire on real old images and let the new banks win (7.4% to 14.6%).
- Decision rule only (no retraining): clipping each class sum to +-T gives old 81.6 / new 81.8; adding a fixed offset to the old-class sums gives a clean trade-off: +5: all 82.8, old 83.7, new 81.4; +10: all 82.9, old 85.9, new 78.4; +20: old 88.8, new 71.9. The best balanced point (about 82.9 overall) is at the level of joint training (about 82 to 83.5, unstable), so the gap is mostly an operating-point choice, not missing information.
- Self-calibration failed: the chip tried to pick the offset from new-class training images and dreams of the old classes. Dreams were classified as old 99.9% of the time (offset -5 to +30), so they carry no information about the hard old/new boundary; it picked -5 (old 77.1). The dreams are too easy: clause-forced dreams score far above any real image.
- Not measured: how much of the old-class drop is inherent (Shirt joins T-shirt, Pullover and Coat in the same cluster, so old accuracy must fall in any 10-class model); a stable joint reference with the same clipped scoring.
- Still open: dreams that sit near the boundary (hard dreams), and a label-free rule for the old/new operating point.

### Hard dreams and a label-free offset rule: FAILED (26 Oct, SIMULATED; `staged_hard.py`, `staged_hard.log`)

The chip imagines a mixture of an old and a new class (bit by bit from their stored frequencies), keeps it only if it is unsure (scores within 10), and learns the difference (label class told "mine", other class told "not mine"; only the veto banks and new banks learn). Three rounds of 20,000 unsure dreams, then an offset chosen so that hard-old and hard-new dreams are classified equally well, with no labels and no real images.

| | all ten | old | new | Shirt recall |
|---|---|---|---|---|
| before | 81.9 | 80.6 | 84.0 | 0.506 |
| after 1 / 2 / 3 rounds | 79.1 / 80.4 / 79.4 | 78.4 / 88.4 / 86.9 | 80.3 / 68.3 / 68.1 | 0.394 / 0.229 / 0.016 |
| after 3 rounds + label-free offset (-10) | 79.1 | 84.5 | 71.0 | 0.088 |

- Old classes recover (to 88 at best) but the new classes pay more, and Shirt collapses (0.506 to 0.016). Overall accuracy falls from 81.9 to 79.4. The mixture dreams of T-shirt, Coat and Pullover teach the Shirt bank "not mine" on images that look like real Shirts, which they are not.
- The label-free offset rule picked -6 and -10, the wrong direction (fixed offsets of +5 to +10 were better before and after). Equalising dream accuracy tells nothing about real accuracy, because independent bit frequencies do not reproduce the structure of the real boundary.
- Conclusion: dreams built from per-bit frequencies cannot carry the Shirt versus T-shirt/Coat boundary. Better imagination needs structure (dreams drawn from the clauses and the code, with correlations), or a few real stored hard examples (not exemplar-free). Not solved.

Related: [Local layers and neurogenesis](local_growth_staged.md), [Feature-level dreams](frozen_encoder_tests.md), [Our own methods](own_methods_routing.md), [Results index](INDEX.md)
