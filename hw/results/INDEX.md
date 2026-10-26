---
title: Results index
tags: [spark, index, results]
---

# Results index

Labels: MEASURED, SIMULATED, ESTIMATED, PROJECTED. JSON files beside each note hold the raw numbers.

## L Cortex (Phase C, now)

- [Month 3 results](cortex_month3.md): RTL bit-exact, bitstream with timing met, host + demo, 10-stage test (SIMULATED).
- [Month 2 results](cortex_month2.md): memory 137x smaller, one rule, integer chip model + RTL bit-exact (SIMULATED).
- [New conditions for known classes](cortex_new_condition.md): limit found (domain shift) and the context-memory fix (SIMULATED).
- [Brain-strict redesign tests](brain_strict_redesign.md): few-label learning, sleep from inside, on-chip detectors, pruning, and the failures (19 Oct, SIMULATED).
- [Sound chip (raw sound in)](cortex_sound_chip.md): cochlea + general encoder + core in RTL, whole chain bit-exact (SIMULATED).
- [L Cortex vs HDC](cortex_vs_hdc.md): ahead of the closest prior art on digits and sound, level on clothing (SIMULATED).
- [ASIC estimate (SKY130)](cortex_asic_estimate.md): ~18.8 mm2 with open SRAM macros, logic < 1 mm2; bit-exact with the SRAM models (ESTIMATED).
- [Energy estimate](cortex_energy_estimate.md): ~74x less energy per decision, ~200x per learned example incl. sleep (ESTIMATED).
- [Month 2 running log](cortex_month2_log.md): every memory-shrink test, including failures (SIMULATED).
- [Month 1](cortex_month1.md): accuracy gap closed on digits, clothing, spoken words (SIMULATED).
- [First proof](cortex_proof.md): no forgetting, exact merge, few-shot loses (SIMULATED).

## Matrix-free lookup core and real-model drafting (Phase B)

- [Token-level lookup on a real model](token_lookup_real.md): tables tie prompt lookup; chat model 1.04 on prose (MEASURED).
- [Matrix-free predictor](matrix_free.md): lookup tables match the network on bytes, hash corrections (SIMULATED).
- [Size study](size_study.md): shrinking the network before fabrication (SIMULATED).

## L v1/v2 beside a GPU (Phase A)

- [Real 9B model, first test](real_model_test_qwen3.5_9b.md): draft 1.51 tokens/pass, answer mode ~6% (MEASURED).
- [Real 9B model, test 3](real_model_test3_qwen3.5_9b.md): copy 2.12, L 1.58, multi 2.17 (MEASURED).
- [Real 3B model, test 3](real_model_test3_qwen2.5-coder_3b.md): multi 2.28, energy estimate.
- [Activation sparsity on 3B](activation_sparsity_qwen2.5-coder_3b.md): cheap predictor far from oracle (MEASURED).
- [Round 4 limits](round4_limits.md): L's own limits vs decode limits (SIMULATED).
- [System simulation](system_simulation.md): L beside a GPU model.
- [Model accuracy](model_accuracy.md): 41% to 74% byte accuracy (MEASURED in software).
- [Energy estimate](energy_estimate.md): energy per token from operation counts (ESTIMATED).
- [Power simulation](power_simulation.md): switching-activity power, 2.4-6.2x less energy per byte (SIMULATED).
- [Synthesis](synthesis.md): Tang Nano 20K place-and-route.
- [Pre-fabrication verification](prefab_verification.md): SKY130 gate-level checks, 0 mismatches.
- [RTL simulation results](sim_results.md) and [with trained weights](sim_results_trained.md).
- [Sensory node](sensory_node.md): two senses (picture + sound) in one chip, sleep cleaning with the chip's own scores and a neighbour unit, bit-exact; a heard word names pictures with no labels (SIMULATED; CNN reference MEASURED).
- [Counting language model, first test](counting_lm.md): online one-pass character model from hashed counters; 4.8 to 1.8 bits per character as memory grows 8 KB to 8 MB (SIMULATED algorithm test).
- [End to end power, encoder included](end_to_end_power.md): picture-to-answer energy and power, chip layout estimate against the measured GPU (about 40 uJ against 0.3 to 69 mJ).
- [Lossless table storage](table_storage_lossless.md): trained tables are 54 to 71% non-zero and use their full widths; ideal lossless coding saves at most 1.7 times (SIMULATED).
- [Counter width against accuracy](bits_vs_accuracy.md): fewer bits cost accuracy, more on clothing than digits; the shipped widths sit near the knee (SIMULATED).
- [Multi-chip counting language model](multichip_lm.md): the 8 MB table split over 1 to 64 chips; traffic, load balance, latency and energy per token (SIMULATED, assumptions stated).
- [Hot-row copies](hot_rows.md): copying 0.02% of the table to every chip removes the load imbalance (2.12 to 1.06 at 64 chips) and cuts remote lookups to 56% (SIMULATED).
- [Shrinking a standard network](compress_mlp.md): a 917 KB MLP shrinks to 115 KB (4-bit) with no measurable loss; at equal memory it beats L Cortex on clothing accuracy (SIMULATED).
- [Staged learning of a standard network](staged_mlp.md): the 4-bit and float MLP both end near 20% after five stages; L Cortex keeps 81.5 to 94.2% (SIMULATED).
- [Neural baseline for the counting language model](neural_vs_counting_lm.md): a small neural model beats the counting model at equal memory up to ~0.5 MB; the counting model only wins with more memory (SIMULATED, failure recorded).
- [Tang Nano 20K preparation of the tile](tile_board_prep.md): single-tile board top passes a UART simulation and synthesises into 1,014 cells + 32 block RAMs (64 KB); not run on a board yet.
- [Where L Cortex loses on clothing](clothing_confusion.md): Shirt/T-shirt/Pullover/Coat limit all-at-once; staged loss falls on similar pairs (SIMULATED, one seed).
- [Specialist for Shirt/T-shirt/Pullover/Coat](shirt_specialist.md): second decision with the same code gains nothing; finer detectors give +1.7 within the group, +0.7 overall at 4x the code (SIMULATED, one seed).
- [Second sense for Shirt against T-shirt](shirt_second_sense.md): oracle-label experiment, NOT a recognition gain (a spoken name is the label); kept as a record with a correction at the top.
- [Shirt against T-shirt on real colour photos](shirt_real_photos.md): colour lifts L's Shirt recall 61.0 to 79.6 on the pair (level with a CNN), not on the 4-way task; no label at test time (SIMULATED, small real data set).
- [L deployed table size against accuracy](l_deployed_memory.md): 11 KB at 2 bits per entry still gives 88.65% on clothing, about 10x smaller than the 4-bit MLP for 0.9 points less (SIMULATED).
- [Fair continual-learning baselines](staged_replay_baselines.md): replay with 200 images per class (1.5 MB) matches L's staged accuracy; EWC stays at 20%; L's edge is about 10x less memory (MEASURED, 3 seeds).
- [Clothing accuracy round: features and readout](clothing_features_round.md): limit is the single binary layer with a linear readout (~90%); conjunctions chosen by counting add +0.8 to +0.9 at 2 to 5x memory; Shirt stays 66 to 74% (SIMULATED).
- [Gated cascade for confusable clothing](cascade_gate.md): second look on the least-sure images: validated +0.9 overall, Shirt recall does not improve (62.5 against 65.8); the first, test-swept numbers were optimistic (SIMULATED, one seed).
- [Few examples: two-brain design](few_shot_two_brains.md): L's counting table is weak below 50 examples per class; class means on L's code give 52% from one example (CNN 42%); a two-brain sum reaches 84.0 at 300 per class (CNN 77.5) (SIMULATED, 3 draws).
- [Shirt recall is an operating-point effect](shirt_operating_point.md): at equal overall accuracy a CNN gets higher Shirt recall only by calling Shirt more often; inside the upper-body cluster L and the CNN are equal (79.0 against 79.2) (MEASURED/SIMULATED).
- [Knockout screen](knockout_screen.md): gene-editing test on detectors; few are reliably faulty, 25% can be dropped at no loss
- [Prune-then-retrain second layer](prune_retrain_second_layer.md): fails the bytes-read criterion; win-lose
- [Shirt new methods round 1](shirt_new_methods_round1.md): flip augmentation, exemplar vote, sub-class tables; none helps within budget
- [Shirt new methods round 2](shirt_new_methods_round2.md): pair detectors and thin-structure cues; fail the criteria
- [Boolean error transport](boolean_error_transport.md): multiply-free error signals through a gate network; best 68 against 81 for float; integer rule failed
- [Local layers and neurogenesis in staged learning](local_growth_staged.md): growth removes overwriting but not competition; local-only error worse
- [Frozen deep gate features in staged learning](frozen_deep_features_staged.md): frozen gate features under the table do not help; L's code alone is best
- [Feature-level dreams and an explicit old-versus-new gate](frozen_encoder_tests.md): feature dreams keep old classes but weaken new ones; the gate is limited by closed-set accuracy
- [Difference-learning ideas for Shirt](shirt_difference_layers.md): residual layer, split where confused, label-free contrastive gates; all failed, with reasons
- [Connected structure (the DNA idea)](connected_structure.md): counted neighbour-conditioned class models; connection adds real information and is continual by construction
- [Tsetlin-style clause learner](tsetlin_clause_learner.md): local feedback, no error passing; 86% with tiny clauses, Shirt AP 0.65, still rising
- [L-Deep attempts](ldeep_attempts.md): shared gate trees by error passing collapse; trees chosen by counted information reach 84%, no gain on L's code
- [MEM-C1 table compression](table_compression_mem_c1.md): difference-only pruned table; only 10 to 25% saving at 10 classes, pays at scale
- [Sparse-by-construction table (option B)](sparse_table_option_b.md): slots and sketch; free at 10 classes, 3 times fewer reads costs 2 to 3 points at 47
- [Our own methods: retrieve-then-rerank and routed clauses](own_methods_routing.md): reads only where they pay; routed clauses keep the whole gain at 30% of the clause cost
- [Energy and tile mapping of the best version](best_version_energy_tiles.md): x3.8 of L on every image, x1.85 routed (ESTIMATED); fits 2 tiles
- [Append-only clause banks in stages](append_only_clause_staged.md): old banks intact but old accuracy 90 to 64 (83.5 with frequency dreams); competition remains, not solved
- [Real depth: second clause layer](clause_depth_layer2.md): works alone (+0.9) but adds only +0.1 to +0.2 in the system; not worth its cost
- [Weight sharing (convolutional clauses)](clause_weight_sharing.md): local rule works but no gain on aligned clothing (+0.2 to +0.4; raw pixels 68 to 75%)
- [Hypothesis loop (propose, test, keep)](hypothesis_loop.md): works as a loop, no gain on Shirt in three proposal variants; missed Shirts are not separable by short conjunctions
- [Composition, first test (relations)](composition_relation_test.md): relation code generalises to unseen classes (70 to 73%) but a plain overlap threshold gets 79%

Related: [Home](../../README.md), [Project memory](../../docs/PROJECT_MEMORY.md)
