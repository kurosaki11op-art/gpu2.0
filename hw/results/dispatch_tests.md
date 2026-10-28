---
title: Dispatch tests - early partial margin, false wakes, and the break-even for gating a layer
tags: [spark, result, simulated, estimate, dispatch, architecture]
---

# Dispatch tests (28 Oct 2026)

The founder's dispatch decision ([one chip, three layers, section 6](one_chip_three_layers.md)): Cortex reads its evidence step by step, exits early when sure, and wakes the bigger layer when not (rules 2 and 3). Three tests on the shipped L code (4,608 bits, shipped table, 10,000 test images, accuracy 88.85). Script and log: [dispatch_tests.py](../brain/experiments/month5/dispatch_tests.py), `dispatch_tests.log`. (a) is SIMULATED on real data; (b) and (c) are arithmetic on those rates with ASSUMED energy figures (stage-2 cost 10.7 nJ, wake energy 0.1 to 100 nJ, 60 pW per bit leakage, retention saving 98% from a paper's claim not verified, decision 6 us). Reference reading was not possible (see [dispatch research](../../docs/research/dispatch_research.md)).

## (a) Does a partial margin predict who the final rule would route? (SIMULATED)

Read a fraction f of the code bits, take the margin of the partial scores, wake the least-sure share w. The final route set is the least-sure 20% by the shipped margin. Random bit order (which hardware can do, since each position's detectors are independent):

| bits read | wake share 20%: final-routed images missed | wake share 40%: missed | of those woken at 40%, not needed | accuracy of the early answer on the 60% not woken (full read gives) |
|---|---|---|---|---|
| 10% | 67% | 40% | 70% | 0.795 (0.923) |
| 25% | 58% | 28% | 64% | 0.911 (0.941) |
| 50% | 39% | 9% | 55% | **0.967 (0.968)** |
| 75% | 18% | 0.3% | 50% | 0.983 (0.983) |

Reading in image order (top rows first) is much worse (at 50% of bits, 69% missed at 20% wake): the first rows say little about the class, so the order of reading matters.

## (b) False wakes against saved delay (ESTIMATED)

At half the bits and a 40% wake share, 55% of the woken images were not routed by the final rule: wakes cost the stage-2 energy plus the wake energy each. Meanwhile the 60% not woken are as accurate as the full read (0.967 against 0.968) and cost half the reads. So **early exit works for Cortex itself; early waking of the bigger layer does not**: to catch most of the images the final rule would route, the partial read must reach 75% of the bits, leaving little delay to hide. The delay actually hidden by a predictive wake was not measured (no timing model); this test only measured rates. Caveat: "the final rule's route set" is itself a threshold on a noisy margin, so missed and false wake rates overstate the harm; the direct test (system accuracy and energy with the predictive wake) is not yet run.

## (c) Break-even for gating a layer (ESTIMATED, assumed inputs)

A 262 KB layer (Deep's weights and state) leaks about 0.129 mW powered; a retention mode would save 0.126 mW. Break-even idle time equals wake energy divided by that: 0.8 us at 0.1 nJ, 7.9 us at 1 nJ, 79 us at 10 nJ, 792 us at 100 nJ. Mean gap between wake requests is the decision time divided by the share woken: 30 us at 20% woken, 60 us at 10%, 120 us at 5%. Net energy per image: gating saves under 1 nJ of about 32 nJ (about 2%) when wake energy is 1 nJ, **costs more than staying powered at 10 nJ (34.1 against 32.7 nJ at a 20% wake share), and much more at 100 nJ**.

## What it means (ESTIMATED / SIMULATED)

1. **At this chip size, most of the saving is not computing, not gating.** Idle leakage of the whole layer's memory is about 0.13 mW, so powering it off saves about 2% and can lose if the wake costs 10 nJ or more. Gating pays only for layers that are much larger or idle for milliseconds.
2. **Rule 2 with early exit is supported.** Reading half the bits in scattered order and exiting when the margin is big loses 0.1 point on the images it answers and saves about half the Cortex reads for 60% of images.
3. **Rule 3 (predict need early to wake sooner) is not supported by this test.** A partial margin is a weak predictor until most bits are read. The delay benefit remains unmeasured; keep it as an open hypothesis, not a design feature.
4. **The wake energy of a layer is the number that decides,** and we do not know it: it needs a layout or a circuit estimate of restoring Deep's domain.

## Next

Measure the system directly (accuracy and energy with early exit plus a threshold wake, using the real second pass), find a better early predictor than the plain partial margin (for example margin growth between two reads), and estimate the wake energy from a layout of the power switches and retention cells.

Related: [Results index](INDEX.md), [One chip, three layers](one_chip_three_layers.md), [Routed second pass](routed_second_pass.md), [Dispatch research](../../docs/research/dispatch_research.md)
