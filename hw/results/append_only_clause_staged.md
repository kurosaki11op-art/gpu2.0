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

Related: [Local layers and neurogenesis](local_growth_staged.md), [Feature-level dreams](frozen_encoder_tests.md), [Our own methods](own_methods_routing.md), [Results index](INDEX.md)
