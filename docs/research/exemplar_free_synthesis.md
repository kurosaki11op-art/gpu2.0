---
title: What 25 papers say about learning new classes without overwriting and without stored images (25 Oct 2026)
tags: [l, research, synthesis, continual-learning]
---

# Synthesis: exemplar-free class-incremental learning, read in full (25 Oct 2026)

Source notes (full-text reads; numbers are the authors' reported figures, not reproduced by us): [A](papers_notes/exemplar_free_papers_a.md) FeTrIL, SDC; [B](papers_notes/exemplar_free_papers_b.md) SSRE, EFC; [C](papers_notes/exemplar_free_papers_c.md) FeCAM, ADC; [D](papers_notes/exemplar_free_papers_d.md) C-FSCIL, AdaGauss, survey; [E](papers_notes/exemplar_free_papers_e.md) generative and feature replay; [F](papers_notes/exemplar_free_papers_f.md) RanPAC, APER, SLDA, FSA; [G](papers_notes/exemplar_free_papers_g.md) TOPIC, FACT, CEC, iCaRL; [H](papers_notes/exemplar_free_papers_h.md) Neurogenesis DL, Expert Gate, DER, FOSTER; [I](papers_notes/exemplar_free_papers_i.md) Forward-Forward, local rules; [J](papers_notes/exemplar_free_papers_j.md) tiny memories, GEM, A-GEM, survey; [K](papers_notes/exemplar_free_papers_k.md) SDM, FlyModel, sparse associative memories; [L](papers_notes/exemplar_free_papers_l.md) novelty and open-set detection. Not read: GDumb (site blocked), brain-inspired replay journal version, MEMO.

## What the papers agree on

1. **Nothing that learns features and forgets nothing exists without either stored samples or a frozen diverse encoder.** With zero stored samples learned representations collapse to chance (EWC, SI, LwF about 10% on MNIST at one class per task); what survives is a fixed or frozen encoder plus per-class statistics (RanDumb 98.3 MNIST, 55.6 CIFAR-10). With a small buffer the gap closes fast: class-incremental MNIST 81.2 at 10 per class and 91.0 at 50 per class against 98.3 joint ([J](papers_notes/exemplar_free_papers_j.md)).
2. **Class-incremental learning splits into within-task prediction and deciding old versus new** (Kim et al., Theorem 4: a good per-task out-of-distribution detector is necessary). Our measured failure (new nodes absorb old images) is exactly this half ([L](papers_notes/exemplar_free_papers_l.md)).
3. **Old-versus-new detection is good when the closed-set classifier is good**: max raw score reaches AUROC 0.986 to 0.993 on MNIST (6 known, 4 unseen), 0.936 on CIFAR-10; closed-set accuracy and open-set AUROC correlate at 0.95; max score beats energy beats softmax. Our 0.73 to 0.81 came from weak stage-1 groups, so it reads as a classifier-quality number, not a limit (INFERENCE).
4. **Replay works at the feature level, not the pixel level**: last-block feature replay 41.5 against pixel-GAN replay 9.7 on CIFAR-100; one Gaussian per class matches iCaRL; replaying noise inputs with old labels does not help ([E](papers_notes/exemplar_free_papers_e.md)). Our dreams were pixel-level, which is the weaker level.
5. **Associative, per-class writes avoid hijacking** (FlyModel: sparse 0.64 against dense 0.07 on MNIST-20; subtracting from wrongly predicted classes lets the newest class hijack shared units) ([K](papers_notes/exemplar_free_papers_k.md)). L's counting table already works this way.
6. **Frozen features with sum statistics do not forget** (RanPAC, APER, SLDA, FSA); most of RanPAC's gain over plain class means (92.2 against 83.4 on CIFAR-100) comes from decorrelating with a Gram inverse, which is dense; random expansion helps only with a nonlinearity and needs width above about 1,250 ([F](papers_notes/exemplar_free_papers_f.md)).
7. **Freezing the embedding matters a lot in few-shot class-incremental** (CEC 49.1 and FACT 52.1 against TOPIC 29.4 last-session on CIFAR-100); FACT reserves room with virtual prototypes made by mixing two real classes. No paper tests a small base set such as 6 of 10 classes ([G](papers_notes/exemplar_free_papers_g.md)).
8. **Growth is not enough**: DER's extra "new versus all old" output adds +2.1 while expansion adds 11.4, but its negatives come from exemplars; FOSTER's confusion matrices show fine-tuning sending almost everything to new classes (our failure). Expert Gate makes the decision explicit with a per-task autoencoder (gate accuracy 97.6% over 6 tasks) but on pre-trained ImageNet features and separate datasets ([H](papers_notes/exemplar_free_papers_h.md)).
9. **Local rules do not forget less by themselves** (SFFA class-incremental without replay near 20%, like backprop); greedy layer-wise training with a deeper local head (k=3) matches end-to-end on ImageNet (67.6 against 67.9 top-1), k=1 is 1.4 behind on CIFAR-10. Our 8 to 15 point local gap may be head capacity ([I](papers_notes/exemplar_free_papers_i.md)).

## What this changes in our plan (decisions, in order)

| Finding | Test it suggests (small, CPU, binary) |
|---|---|
| Replay at feature level | Dream at the first gate layer's output (class bit rates and mixtures there), freeze layer 0, grow only upper layers; compare with pixel-level dreams |
| Old-versus-new from a strong closed-set classifier, raw max score | Re-measure the gate AUROC with a better stage-1 classifier and max raw score, margin, active-bit count; then use it as the explicit old/new decision |
| Head capacity | Local learning with k=1 and k=2 auxiliary heads on the integer gate network |
| Frozen code plus statistics | Counting heads on a frozen binary code with a matrix-free substitute for the Gram inverse (centring and size normalisation; diagonal weights by lookup) |
| Forward compatibility | Spare count rows made from mixed pairs of base classes (FACT) |
| Buffer size | Staged learning with 1 to 100 stored binary codes per class, to find where it matches joint training |

Related: [Paper notes index](papers_notes/INDEX.md), [Docs index](../INDEX.md), [Forgetting-free adaptation papers](papers_notes/forgetting_free_adaptation_papers.md), [Local layers and neurogenesis](../../hw/results/local_growth_staged.md)
