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

### Think loop by counting, no dreams (26 Oct, SIMULATED; `staged_think.py`, `staged_think.log`)

Compare stored per-class bit frequencies of an old class c and a new class n (real counts, no sampling): bits common in n and rare in c become one-literal vetoes under c. A veto that fires only if its literal holds can fire on at most f_c(literal) of c's own images, so the damage to the old class is bounded before the veto is installed (admit only if f_c <= RHO). No training, no dreams, one counting pass. Same saved new banks as above (new banks only: 75.8 overall, old 86.1, new 60.4, Shirt recall 0.346).

| RHO, vetoes per old/new pair | all ten | old | new | Shirt recall | vetoes firing on own class |
|---|---|---|---|---|---|
| 0.01, 20 | 76.3 | 85.6 | 62.4 | 0.371 | 0.54 |
| 0.03, 75 | 77.4 | 82.0 | 70.5 | 0.454 | 4.9 |
| 0.10, 20 | 79.0 | 80.6 | 76.5 | 0.494 | 5.8 |
| 0.10, 75 | 77.1 | 71.7 | 85.2 | 0.591 | 18.5 |
| 0.30, 20 | 77.1 | 69.5 | 88.4 | 0.691 | 17.7 |

- The bound holds (own-class firing stays under vetoes x RHO), so the damage to old classes is predictable, which the dream-trained vetoes could not offer. Best +3.2 over no vetoes, below the learned vetoes (81 to 82): single literals are too weak.
- It is again a trade-off along one axis (old falls as new rises); the chip can read the cost of each veto in advance, which is the first step to a label-free operating-point rule (admit vetoes until the guaranteed expected damage reaches a budget). Not built.
- Next: conjunctions of literals chosen against the real new images (specific, same bound with the rarest literal), and the damage budget rule.

### Boundary memory: a few stored real images per old class (26 Oct, SIMULATED; `staged_replay.py`, logs `staged_replay_<E>_<pick>.log`)

After stage 1 the chip keeps E real images per old class: the E it was most unsure about ("doubt": smallest margin) or E random ones (control). In stage 2 they replace the dreams (negatives for the new banks; "still mine" for the old veto banks). 2 epochs per stage, one seed, offset 0 / +10 added to the old-class sums.

| stored per old class | picked by | vetoes | all ten (offset 0 / +10) | old (+10) | new (+10) | memory |
|---|---|---|---|---|---|---|
| 2 | doubt | yes | 51.0 / 53.5 | 24.5 | 96.9 | 25 KB |
| 5 | doubt | yes | 55.2 / 59.1 | 34.1 | 96.8 | 62 KB |
| 5 | random | yes | 60.4 / 65.1 | 44.7 | 95.8 | 62 KB |
| 20 | doubt | yes | 71.0 / 76.5 | 68.1 | 89.2 | 251 KB |
| 20 | random | yes | 80.4 / 82.4 | 81.7 | 83.5 | 241 KB |
| 20 | random | no (new banks only) | 73.8 / 69.4 | 89.2 | 39.8 | 241 KB |
| reference: frequency dreams + veto | 81.9 / | 80.6 | 84.0 | about 0 |
| reference: joint training | about 82 to 83.5 | | | |

- **2 to 5 stored images fail badly**: the vetoes learn the few stored images as exceptions and then reject almost every other real old image (old accuracy 25 to 45%). The test of "a handful of boundary images" is NEGATIVE.
- **Doubt-picked images are worse than random ones** (76.5 against 82.4 at 20): the most unsure images are outliers and ambiguous cases and teach the wrong boundary.
- **20 random per class reaches the dream and joint level (82.4) but costs 241 KB** as bit lists (about 2 KB per image), nearly three times the 84 KB table, so the memory advantage over replay disappears at this size.
- Result: stored examples are not a cheap proper fix. They work only at a size that removes the memory advantage; the dreams reach the same accuracy for about no memory. The remaining old-class gap is therefore not an information problem that a few examples solve.

### Tree-structured dreams and the stable joint reference (26 Oct, SIMULATED; `staged_replay.py` PICK=tree|freq, `staged_joint_ref.py`)

Dream banks of 3,000 imagined images per old class, either from independent bit frequencies (freq) or from a model where each bit depends on the earlier bit it shares the most information with (tree; about 6,000 conditional counters per class), used in place of stored images in the same pipeline (new banks learn old dreams as negatives, old veto banks learn new images as "not mine" and dreams as "mine"). Joint = all ten classes together, same code and scoring, 4 epochs. Old-class offset sweep shows the whole old/new frontier.

| 4 epochs per stage | offset | all ten | old | new | Shirt recall |
|---|---|---|---|---|---|
| frequency dreams + vetoes | 0 | 81.3 | 79.7 | 83.9 | 0.566 |
| frequency dreams + vetoes | +10 | 82.4 | 85.7 | 77.5 | 0.411 |
| tree dreams + vetoes | 0 | 81.1 | 81.9 | 80.0 | 0.528 |
| tree dreams + vetoes | +5 | 81.4 | 84.9 | 76.0 | 0.444 |
| joint training (same code) | 0 | 85.8 | 85.2 | 86.7 | 0.617 |
| joint training | +10 | 85.5 | 88.5 | 81.1 | 0.425 |
| (2 epochs per stage, frequency dreams, 18,000 imagined) | 0 / +10 | 82.7 / 82.0 | 85.3 / 88.6 | 78.9 / 72.2 | 0.376 / 0.214 |

- **Dream structure is not the lever.** Tree dreams (bits that depend on each other) give the same accuracy as independent-bit dreams (81.1 against 81.3). Imagining better does not close the gap.
- **The gap to joint training is about 3 to 4 points overall, all on the new classes.** At equal old-class accuracy (about 85), joint gets new 86.7 and the staged chip 78.9 to 80.0; Shirt recall 0.617 against 0.38 to 0.53.
- **Why:** a new class is learned against the other new classes and against imagined old classes, never against real old images. Shirt is defined by what separates it from T-shirt, Pullover and Coat, and with those images gone that boundary cannot be observed; no imagination from per-class statistics reproduces it. The old classes are protected (storage never forgets; accuracy 85 against 90.8 before Shirt joined, the rest being the harder 10-class task), the cost falls on the late class.
- Staged and joint land on the same frontier shape, so the choice of operating point (offset) is a free trade, and the label-free rule for it is still open.
- Honest summary of the fix attempts: frequency dreams, hard dreams (failed), stored images (work only at 241 KB), counted vetoes (bounded, weak), tree dreams (no gain). Best staged result 82 to 83 against 85.8 joint.

### Stored-image scaling with more training, and unfrozen rehearsal (26 Oct, SIMULATED; `staged_replay.py` EPS=4, `staged_rehearse.py`, logs `staged_replay4_*.log`, `staged_rehearse_*.log`)

User direction: memory and power stay primary but the goal is 10 to 20 times better than a GPU, not 100 times, so the cost of the continual-learning fix has to be measured, not avoided. Two designs with real stored images per old class (random pick), 4 epochs: (A) frozen old banks + veto banks (as above); (B) unfrozen rehearsal: all ten banks keep learning with the ordinary local clause rule on a class-balanced stream (new classes from full data, old classes from the stored images only). Joint reference (same code, 4 epochs): 85.8.

| stored per old class (6 old classes) | (A) frozen + vetoes, best offset | (B) unfrozen rehearsal, +10 offset |
|---|---|---|
| 20 | 81.1 (2-epoch run: 82.4) | peaks 82.0 at 50k steps, then collapses to 69 (old 52) |
| 50 | 81.8 | - |
| 100 | 82.7 | 84.8 (old 84.7, new 85.0) at 150k steps; 83.4 at offset 0 |
| joint training | 85.8 | |

- **Unfrozen rehearsal with 100 stored images per class gets within one point of joint training (84.8 against 85.8)**; the frozen veto design stalls at 82 to 83 however many images it gets. So "frozen" is part of the loss, as the user argued: letting the old banks keep learning under rehearsal recovers about 2 points that no veto design did.
- **Too few stored images overfit.** With 20 per class the clauses learn the stored images as exceptions: accuracy peaks early and then collapses (old 34 to 52%). The stream needs enough distinct images (about 100 per class here) or a regulariser.
- **Memory price (ESTIMATED).** 100 images per old class, stored as the detector code (about 580 active bits, about 0.5 KB delta-coded) is about 50 KB per old class, 300 KB for six, against an 84 KB table. At 1,000 classes that is about 50 MB. Plain replay baselines needed 200 per class; this is about half that, not the 40 times less I earlier hoped for. So the replay route reaches accuracy at a memory cost that is not yet a 10 to 20 times win; it needs cheaper exemplars (shared, compressed, or chosen to cover the class with fewer images).

### Cheaper exemplars: recombination, k-means picks, plasticity limit, and a label-free offset (26 Oct, SIMULATED; `staged_rehearse2.py`, logs `staged_rehearse2_*.log`)

Unfrozen rehearsal as above (150,000 steps, 6 old classes, joint reference 85.8). Changes: (1) PICK=kmeans chooses the stored images nearest to cluster centres instead of random ones; (3) AUG=cross draws each rehearsal image as a recombination of two stored images of the same class (each bit where they differ taken from either parent) with 2% bit noise, so a handful of images cannot be memorised; PL slows the old banks' learning.

| stored per old class | picked | augmentation | best offset: all / old / new | note |
|---|---|---|---|---|
| 20 | k-means | none | 67.9 (+10) | collapses, as with random |
| 20 | k-means | recombine | 81.3 early, 77.9 late (+10) | centres are atypical; worse than random |
| 20 | random | recombine | 84.0 (+30): 86.0 / 81.0, and 82.9 (+30) on a rerun | stable between 50k and 150k steps |
| 20 | random | recombine, plasticity 0.3 | 79.6 (+10) late | slowing the old banks does not help |
| 50 | k-means | recombine | 84.3: 84.4 / 84.0 | |
| 50 | random | recombine | 83.8 to 83.6 (+10 to +20) | |
| 100 | random | none | 84.8 (+10) | earlier run, no augmentation |
| joint | | | 85.8 | |

- **The earlier "collapse" was mostly an operating point.** With a wide offset sweep (0 to +40) 20 stored images per class hold 83 to 84 at 50k and 150k steps; the old and new classes just balance at a larger offset (+30) than the +10 first tried.
- **Recombination is what makes few images enough**: 20 per class with recombination (about 83 to 84) matches 100 per class without it (84.8). Memory for 20 per old class is about 10 KB per class, about 60 KB for six, below the 84 KB table (ESTIMATED).
- k-means centres are worse than random images at 20 (typical images matter, not just spread); lowering plasticity does not help.
- **Label-free offset rule works in this run**: the chip picks the offset at which the share of test images it assigns to old classes equals the old classes' share of its own training stream (0.600, known from counters). On the rerun it picks +30 (predicted share 0.609), which is also the best offset (82.9). One run; the earlier run's best offset was +30 as well.
- Run-to-run spread is about 1 point (84.0 against 82.9 for the same setting; the parallel update order is not fixed). Gap to joint training: about 2 points.

### EMNIST-balanced, 24 then 23 classes (26 Oct, SIMULATED, one seed; `emnist_staged.py`, logs `emnist_staged_*.log`)

Second dataset with many classes, to test whether the rehearsal design is a clothing quirk. Clause learner only (120 clauses per class, literals = L's detector code + raw pixel bits; weaker than L's counting table, which gets 88.7 at 24 and 82.9 at 47 classes). Stage 1: classes 0 to 23, 3 epochs (78.5 on those 24 classes). Stage 2: classes 24 to 46 added with unfrozen rehearsal, 200,000 steps, old classes from 20 stored images each (480 images; recombined pairs + 2% noise).

| | all 47 classes | old (24) | new (23) | share predicted old |
|---|---|---|---|---|
| joint training, 4 epochs / 8 epochs (still rising) | 68.2 / 71.2 | 63.0 / 70.3 | 73.7 / 72.2 | 0.46 / 0.52 |
| staged, offset +0 | 66.0 | 58.8 | 73.7 | 0.40 |
| staged, offset +4 (label-free rule's pick) | **67.4** | 66.3 | 68.6 | 0.490 |
| staged, offset +6 | 67.4 | 69.3 | 65.3 | 0.537 |
| staged, offset +10 | 65.0 | 73.8 | 55.6 | 0.638 |

- **The design carries over**: staged learning with 20 stored images per old class reaches 67.4 against 71.2 for joint training with 8 epochs, a gap of about 4 points (about 3.5 against the 4-epoch reference with the same wall-clock), on 47 classes instead of 10. Old classes were not frozen and were never trained on their full data after stage 1.
- **The label-free offset rule again picks the best offset**: matching the predicted old share (0.511 in the stream) selects +4 (share 0.490) or +6 (0.537); both give 67.4, the best of the sweep. The useful offset is small here (+4, against +30 on clothing): the offset scale depends on the clause count and T, which is why a label-free rule is needed rather than a fixed constant.
- Caveats: clause layer alone, not the full L system; joint training is still rising; one seed; stored images are random, not tuned; memory 480 images (about 10 KB per class, ESTIMATED).

### A controller so the chip runs its own loop (26 Oct, SIMULATED; `staged_controller.py`, logs `staged_controller_{sab,clean}_{on,off}.log`)

Built the three missing parts, using only unlabeled signals (an unlabeled probe of 5,000 test images; labels only for scoring on the other 5,000): (4) NOTICE: after every 25,000-step chunk the chip compares the share of images it assigns to each class with the share its own stream implies (1/10 each); if the share distance rises by more than 0.05 over the best so far it undoes the chunk (restores a checkpoint) and halves its step size. (1) DECIDE: it sets the old/new offset by the share rule every chunk, picks the pairs of classes that are most often the top two with a small margin and gives them 3 times the rehearsal and negative-feedback weight, and stops when the share distance has not improved for 2 chunks. (2) COMPARE: the weight on the confused pair makes the clauses of both classes learn from both classes' images (conjunctions through the ordinary clause rule), instead of counting single bits.

| run | what happened | final all ten (old / new) |
|---|---|---|
| sabotage (chunk 3 rehearsal images 45% corrupted), controller on | share distance jumped 0.12 to 0.42, ALARM, chunk undone, step size halved, recovered, stopped itself after 7 chunks | **83.0** (82.6 / 83.5) |
| sabotage, controller off | accuracy fell to 78.1 after the bad chunk and recovered only partly | 81.4 (80.3 / 82.9) |
| clean, controller on | stopped itself after 5 chunks (best 83.6 after chunk 3) | 82.3 (82.0 / 82.6) |
| clean, controller off (8 chunks) | | 83.0 (82.5 / 83.7) |

- **The chip now notices that it went wrong by itself**: the corrupted chunk was caught by the share signal alone (no labels), undone, and the run ended 1.6 points above the run without a controller. This is the first part of the loop that exists inside the chip rather than in my logs.
- **On a clean run the controller does not raise accuracy** (82.3 against 83.0, inside the 1-point run-to-run spread); what it saves is work: it stops after 5 chunks instead of 8.
- Weak spots: the share-matching offset rule is noisy because the share-versus-offset curve is flat near the target (picked +20 to +42 across chunks, the final choice moved accuracy by about 1 point); the effect of the 3x pair weighting alone was not isolated; one seed; the probe is half of the test set (unlabeled), not a separate stream.
- "Think" status: it can now notice, undo, pick what to rehearse and decide when to stop, from its own signals. It does not yet form a hypothesis about why two classes differ.

Related: [Local layers and neurogenesis](local_growth_staged.md), [Feature-level dreams](frozen_encoder_tests.md), [Our own methods](own_methods_routing.md), [Results index](INDEX.md)
