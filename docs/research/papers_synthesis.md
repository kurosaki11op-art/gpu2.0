---
title: Synthesis of the full-paper reading (24 Oct 2026)
tags: [l, research, synthesis]
---

# What the primary papers say about our clothing gap, and what to test

Sources: the five notes in [papers_notes](papers_notes/INDEX.md), read in full from PDF text (numbers UNVERIFIED where marked there).

1. **The gap is mostly a feature gap, not label noise.** Fashion-MNIST irreducible error is about 3 to 4% on the whole test set (Ishida et al., 2202.00395); Shirt/T-shirt's share is not measured. The Cleanlab blog claim is unverified. My earlier "label overlap" reading was wrong.
2. **The Tsetlin results above 91% come from the input code.** FPTM (2508.08350): raw 4-level thermometer + 8 fixed edge maps (Sobel 3, 5, 7 and a line detector, two orientations) in 9 sign-split quantile bits = 59,584 bits per image; 2 clauses per class give 92.18, 20 give 93.19, 8,000 plus 6x augmentation give 94.68. The same learner on a plain 1-bit code gets about 91.2 (CTM, 8,000 clauses). Four booleanisations as a team give 93.0 (Composites). Inference needs only compares and popcounts, so the code can be copied into L. **Test in progress: `fptm_code.py`.**
3. **Weightless networks do not go higher than our one-layer net on Fashion-MNIST:** DWN 89.12% at 7.8 KiB (4 to 10 times smaller than our lookup layer), ULEEN 87.86%. Their value to us is size (a 7.8 KiB model at 89%), through the DWN recipe: 7 quantile thermometer bits per pixel, two LUT-6 layers of 2,000, learnable mapping in layer 1 (+2.2 points), extended finite-difference gradient (+1.1), spectral regularisation (+1.1), 100 epochs.
4. **Only convolutional logic-gate trees reach CNN-like accuracy matrix-free:** LogicTreeNet (2411.04732) MNIST 99.23 to 99.35, CIFAR-10 86.29% at 61 M gates; keys: gate-tree conv kernels with shared gates, OR pooling, residual initialisation (pass-through logit 5), temperature scaled with the square root of the class group, AdamW lr 0.02, fixed edge detectors, a CNN teacher for the big models. No Fashion-MNIST number; the reader estimates the plain difflogic layer at about 1 hour to reimplement and gate-tree convolution at 2 to 3 hours.
5. **Local learning is at our level:** BCPNN 88.9 (MLP 89.5, raw linear 83.5); SoftHebb has no real Fashion-MNIST number; soft coding helps on CIFAR-10 (+several points) but hard WTA wins on MNIST (98.29 against 97.87). Our k=3 soft test (88.65 against 88.85) agrees that soft coding alone does not help here.
6. **Pitch baselines:** class-incremental Split MNIST: fine-tuning 19.9, EWC 20.0, generative replay 90.8, iCaRL (2,000 stored) 94.6, joint 97.9; strongest no-stored-data baselines generative classifier 93.8 and streaming LDA 87.3; Split Fashion-MNIST replay with 200 / 500 / 1,000 images 72.5 / 79.0 / 81.4, joint 84.5. MLPerf Tiny has no continual-learning task and measures energy at the core supply only.

## Order of work from this reading
1. FPTM-style rich code with L's counting readout (running).
2. Difflogic gate network on Fashion-MNIST (recipe known; CPU cost is the limit), then gate-tree convolution if it works.
3. DWN-size model (7.8 KiB at 89%) as a memory point for the pitch.
4. Re-run the staged-learning baselines on one stream with the generative classifier and streaming LDA added.

Related: [Docs index](../INDEX.md), [Paper notes index](papers_notes/INDEX.md), [Failure analysis](../failure_analysis_clothing.md), [Research report](matrix_free_vs_cnn_report.md)
