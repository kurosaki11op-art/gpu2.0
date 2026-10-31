---
title: Docs index
tags: [spark, index]
---

# Docs index

## Now (L Cortex)

- [Error transport design](error_transport_design.md): blame-routed detector learning, designed from our failures; success criteria are win-win only.
- [Claims ledger](claims_ledger.md): every claim about L with a status (tentative, verified, withdrawn, failed) and the rules for stating one.
- [Failure analysis: why L stays behind on clothing](failure_analysis_clothing.md): past failures, causes, literature, ideas in order.
- [Status report 24 Oct 2026](status_report_24oct.md): plain summary of what is done, failed and needed.
- [Who scores 96 to 99 percent and how](research/who_beats_cnn.md): which winners are matrix- and multiply-free, how they win, where we fail.
- [Synthesis of the full-paper reading](research/papers_synthesis.md): what the primary papers say about the clothing gap, in order of work.
- [Matrix-free models against CNN accuracy (research report)](research/matrix_free_vs_cnn_report.md): what Tsetlin, LUT and logic networks reach on MNIST/Fashion/CIFAR, shirt difficulty, pitch baselines; most numbers second-hand.
- [GPU limits against L](gpu_limits_and_L.md): power, heat, water, e-waste, memory wall; what L shows and does not (ESTIMATED).
- [Project memory](PROJECT_MEMORY.md): everything in one place; read first.
- [Journal](journal.md): the step-by-step record.
- [Month 4 board plan](month4_board_plan.md): the steps that turn simulated results into MEASURED ones on the Tang Nano.
- [Overnight report, 15 Oct](overnight_report_2026-10-15.md): summary of the night's work and the board steps for today.
- [Accelerator for L, a skeptical design review](L_accelerator_design.md): profile, microarchitecture, staged path, fair comparison and risks for a dedicated chip for the L language model (a separate project from L Cortex).
- [L hypothesis, falsification and silicon plan](L_hypothesis.md): the testable hypothesis, how it can fail, node, size, material and cost (ESTIMATED).
- [Virtual space: chip vs GPU benchmark](../virtual_space/README.md): one container (or Python environment), your GPU, the chip as its RTL design in a simulator, one table; commands for Windows.
- [Prompt: facts the L accelerator needs](../prompts/L_facts_for_accelerator_prompt.md): paste into an agent inside the L model repo; it measures activity sparsity, ablations, profile and exports golden vectors.
- [L Cortex redesign](cortex_redesign.md): design, AI problems targeted, 6-8 month plan, status.
- [Brain-principles audit](brain_principles_audit.md): the six-point test every process must pass, which processes fail it, and the order of fixes.
- [Project scope](scope.md): what is in and out of scope, agreed with the founder.
- [L Cortex claims sheet](cortex_claims_sheet.md): every claim with its number, label, source and caveat; what not to claim.
- [Research: GPU few-shot and class-incremental tricks](research_fewshot_gpu.md): what GPU systems do for new classes and which integer analogues we tested (19 Oct).
- [Results at a glance](results_at_a_glance.md): one page of the headline results, costs and limits with labels and links (for the pitch).
- [Prior art for L Cortex](prior_art_cortex.md): what is not new (HDC, Loihi 2, replay) and what we can claim.
- [Research: fixing the weak spots](research_weak_spots.md): dreams that keep co-occurrence, few-shot words, clothing gap.
- [Research: detailed routing with SRAM macros](research_openroad_sram_routing.md): why routing failed and the OpenROAD settings that fix it.
- [Research: a new class from a few examples](research_fewshot_class_incremental.md): fixes for old/new bias (imprinting, weight aligning, hippocampus gating).

## Brain research behind the design

- [Brain as a chip](brain_as_chip_research.md): what is known about the brain, what transfers to a chip.
- [How brains compute and move weights](brain_principles_for_spark.md): sparse events, fast/slow memory, predictive coding.

## Phase B: matrix-free lookup core (L-lookup, 12-14 Oct)

- [Lookup core RTL](lookup_core_rtl.md): v1, v2 and token-level cores, block-RAM fit, board facts.
- [Prior art: lookup drafting](prior_art_lookup_drafting.md): prompt lookup and suffix decoding vs our tables.
- [Redesign decision](redesign_decision.md): three outside reviews checked against our numbers.
- [Branch-parallel architecture](branch_parallel_architecture.md): parallel thought branches, what can be proved.

## Phase A: L v1/v2 language chip beside a GPU (9-13 Oct)

- [L architecture](spark_architecture.md): design built around existing chips' weaknesses.
- [AI-development positioning](spark_ai_development_positioning.md): the drafting-accelerator pitch (superseded).
- [Full-stack hardware proposal](spark_full_stack_hardware_proposal.md): fixes for GPU energy, heat and water.
- [Software vs hardware](software_vs_hardware.md): which GPU limits need which fix.
- [Existing chips and think-less design](existing_chips_and_think_less_design.md): competitor chips.
- [Borrowed strengths and hypotheses](borrowed_strengths_and_hypotheses.md): what L borrows, H1-H10.
- [Limitations and sustainability research](limitations_and_sustainability_research.md): GPU/LLM limits, power, water.
- [L v0 model format](spark_v0_model_format.md): trained model format and integer semantics.
- [Hardware claims sheet](hardware_claims_sheet.md): labelled claims for the old pitch.
- [Pitch script](pitch_script.md): speaking and video script for the old deck (superseded by the Cortex script below).
- [Final pitch speaker script (23 Oct, 25-slide deck)](pitch_script_final.md): how to pitch, what to claim and not, slide-by-slide script, 5-minute cut, short answers.
- Printable copies of the final script: `L_pitch_speaker_script.pdf` and `L_pitch_speaker_script.docx` (same text as the file above).
- [L wafer-scale design study](L_wafer_design.md): paper design of a Cerebras-class tiled machine for sparse lookup models, sizing by node (ESTIMATED).
- [Live demo cheat sheet](live_demo_cheatsheet.md): commands and talking points for the chip-vs-CNN test on the laptop GPU.
- [Cortex pitch script](pitch_script_cortex.md): speaking script for the 23 Oct event, slide by slide, with a short cut list (deck: `SPARK_Cortex_pitch.pptx`).
- [Event checklist](event_checklist.md): what to do before the 23 Oct event and what to say / not say.
- [Pitch Q&A sheet](pitch_qa_sheet.md): the questions judges are likely to ask, with honest labelled answers.
- [Short paper](paper_spark_cortex.md): abstract, design, results, cost, limits and related work in two pages, for the paper-style presentation.
- [What the failures taught us](lessons_from_failures_25oct.md): nine lessons and the design they point to (25 Oct 2026)
- [L-Genome design](L_genome_design.md): connected, append-only, growing structure; failure-to-rule map and kill tests (25 Oct 2026)
- [Managing memory as L scales](research/memory_at_scale_synthesis.md): synthesis of the Stanford, Cerebras, Groq, Graphcore, Dojo and in-memory-compute reading; design rules for L's tiles
- [Blackwell, Cerebras and memory physics](research/hardware_landscape_synthesis.md): side-by-side, weak points and where L could differ (25 Oct 2026)
- [Thinking research synthesis and build order](research/thinking_synthesis.md): five parts of thinking, papers read, proposed methods, order (26 Oct 2026)
- [Concept study: convolution](concept_study_convolution.md): why it exists, how it is built, its flaws, our own fix directions and tests (28 Oct 2026)
- [L numeric tile study](L_numeric_tile_study.md): benchmark list (physics, FFT, rendering, LLM, recognition) and an energy model of a memory-on-chip tile against a GPU (ESTIMATED, 28 Oct 2026)
- [L Forge design](L_forge_design.md): the third layer, a GPU-class numeric layer built on our own differences, tile spec, cost at 5 nm and 2 GB, acceptance tests (design hypothesis, 28 Oct 2026)
- [Build plan, December to January](L_build_plan_dec_jan.md): weeks, gates, deliverables and cuts for finishing L Deep and L Forge before the February event (ESTIMATED, 28 Oct 2026)
- [Status, 28 Oct 2026](L_status_28oct.md): what exists for L Cortex, L Deep and L Forge, the evidence, the gaps and what is needed from the founder
- [Claims register](claims_register.md): what may be said about L with its label and evidence, and what may not (28 Oct 2026)
- [Measurement protocol](measurement_protocol.md): the GPU baseline script, board power procedure and the three-layer FPGA build, to turn estimates into MEASURED numbers (28 Oct 2026)
- [FPGA board decision](fpga_board_decision.md): Tang Mega 138K primary, Arty A7-100T fallback, three checks before paying and the bring-up plan (28 Oct 2026)
- [Concept study: GPU and memory](concept_study_gpu_and_memory.md): how a GPU, SRAM, DRAM and HBM are built, their flaws, density options and our own directions (28 Oct 2026)
- [Dispatch research](research/dispatch_research.md): early exit and power gating references, abstract level only, arXiv unreachable (28 Oct 2026)

- [GPU problem analysis](gpu_problem_analysis.md): each problem of today's GPUs against what L shows, with labels, accuracy position and coverage of GPU workloads (30 Oct 2026)

- [Lessons from L version 1](lessons_L_v1.md): wins, failures and what the new start must do differently (30 Oct 2026)

- [Diagnosis and learned router, result](../new_start/step9_router_result.md): MEASURED; router B fails R1 and R2 on both slices, stop rule applied: language cascade claim dropped (31 Oct 2026)
- [Diagnosis and learned router, bars](../new_start/step9_router_plan.md): bars R1-R3 written before the run; CPU in the cloud container (31 Oct 2026)
- [Cascade on real language models, pair A on the RTX 3050](../new_start/step8_pairA_gpu_result.md): MEASURED; stage A agrees with CPU (C1, C3 fail); live energy 29-41% lower gross, speed gain small (loop overhead), fidelity metric flawed (31 Oct 2026)
- [Cascade on real language models, pair A CPU result](../new_start/step8_pairA_cpu_result.md): margin trigger fails C1 (7.4% worse than the large model at 30% escalation) and C3 (1.6x random, bar 2x); learned router proposed (31 Oct 2026)
- [Cascade on real language models, bars and test plan](../new_start/step8_cascade_lm_plan.md): small plus large model, margin-gated; bars written before any run, script included (31 Oct 2026)
- [Our GPU, M2 result](../hw/gpu/M2_result.md): cycle and energy model validated against the simulator (counts, cycles, decode identical) and within 4% to 17% of the earlier energy model for a 1B decoder; latency 2.4x to 5.7x faster than the earlier latency model (bar fails) (31 Oct 2026)
- [Our GPU, M1 fix result](../hw/gpu/M1_fix_result.md): mixed precision (5 of 13 tensors with INT16 activations, 32% of MACs) meets the 99% bar on both sets; the next-character loss shows W8A8 was already within 0.002 nats of fp32 (31 Oct 2026)
- [Our GPU, M1 result](../hw/gpu/M1_result.md): the functional simulator runs a CNN and a transformer on a tile mesh and matches PyTorch (SIMULATED); bars a and c pass, b passes for INT8 weights and misses in W8A8 on the transformer (98.73%) (31 Oct 2026)
- [Charter: our own GPU](own_gpu_charter.md): scope (inference first, then compiler, then training), what the evidence supports, milestones M1-M5 with pre-set bars (31 Oct 2026)
- [Data and quotes to obtain before manufacturing](manufacturing_data_requests.md): ten figures the cost, energy and capacity models still assume, with who can answer and which result each decides (31 Oct 2026)
- [Redesign test 5, result](../new_start/step20_k5_result.md): hidden layer on the code gives 90.0% clothing and 98.75% digits (bars K5-a, b fail; c, d, e pass); end of the L accuracy work (31 Oct 2026)
- [Redesign test 5, bars](../new_start/step20_k5_plan.md): a hidden layer (4,608-256-10, sparse first layer) on the code; bars written before the run (31 Oct 2026)
- [Redesign test 4, result](../new_start/step19_k4_result.md): prototype layer plus ridge at full data stays at 88.7% clothing (code ceiling for linear readouts); K4-a, b, d, e fail (31 Oct 2026)
- [Redesign test 4, bars](../new_start/step19_k4_plan.md): prototype layer (3,000 prototypes learned without labels) plus closed-form readout at full data; can L reach a tuned network on clothing? bars written before the run (31 Oct 2026)
- [Row K test 3, result](../new_start/step18_k3_result.md): ridge readout and prototypes from unlabelled images close most of the few-label gap from 300 labels (+3 to +5 pts over every baseline); K3-a missed by 0.02 pts at 100 labels, K3-b, c, d pass (31 Oct 2026)
- [Row K test 3, bars](../new_start/step18_k3_plan.md): the few-label weakness, methods using unlabelled images (cluster features plus ridge readout); bars written before the run (31 Oct 2026)
- [Row K test 2, result](../new_start/step17_k2_result.md): K2-a, b, c pass, K2-d fails (MNIST 1,000 labels -1.9 pts); less training compute holds (17x-352x, conservative), less data does not (L 6-14 pts behind at 100-300 labels) (31 Oct 2026)
- [Row K test 2, bars](../new_start/step17_k2_plan.md): stronger baselines, more seeds, MNIST as a second task, conservative energy accounting (L x28); bars written before the run (31 Oct 2026)
- [Row K test 1, result](../new_start/step16_k1_result.md): MEASURED accuracy, COUNTED compute; all three bars pass (L 88.85% vs network 89.4% at 60,000 labels, ahead at 1,000-10,000; about 200x to 5,000x less training energy); basic baseline, one task (31 Oct 2026)
- [Row K test 1, bars](../new_start/step16_k1_plan.md): training cost to reach an accuracy, counting rule against gradient descent on Fashion-MNIST; bars written before the run (31 Oct 2026)
- [Row I, bottom-up packaged-chip cost](../new_start/step15_packaged_cost_result.md): an 11 W chip needs no CoWoS/HBM/cold plate; bottom-up $480 per chip gives 2.74x like for like (central), bar met, resting on one unsourced $150 for package/board/power/cooling (31 Oct 2026)
- [Row I, price-cut test](../new_start/step14_price_cut_result.md): advantage 1.94x after a 40% Nvidia cut (bar 2x missed), erased at about 69% (central) or 51% (worst); energy and speed advantages are not price-dependent (31 Oct 2026)
- [Row I, buyer price view](../new_start/step13_buyer_price_result.md): at 2x markup the buyer pays 3.2x less per token (central) but only 1.26x less in the worst corner (bar 2x missed); the win comes from the GPU margin; row I reopened as conditional (31 Oct 2026)
- [Rows I and J, final disposition](../new_start/step12_close_i_j_final.md): J closed (passes; GPU energy floor confirmed by one measurement), I closed as failed (no cost advantage at any speed floor), reopen condition stated (31 Oct 2026)
- [Memory technology study](../new_start/step11_memory_technology_study.md): scan says the cost bar needs about 4.2x SRAM density at SRAM-like price; eMRAM closest by cell size but read energy and cost unknown; DRAM-PIM fixes cost but is compute-starved (31 Oct 2026)
- [Capacity levers and the cost failure](../new_start/step10_capacity_levers_result.md): 4-bit KV cache and fewer weight bits help both machines equally; cost bar fails in every combination; requirement derived: about $215/GB all-in fast memory (31 Oct 2026)
- [Cost like for like](../new_start/step7_cost_basis_result.md): the cost comparison used our cost against the GPU selling price; like for like the SRAM system is at cost parity at best (1.02x central, 0.61x worst); the blocker is SRAM about $175/GB vs HBM about $17/GB (31 Oct 2026)
- [SRAM bank energy model](../new_start/step6_sram_energy_result.md): all-in weight read 0.08-0.55 pJ/bit, worst-case energy bar passes on the model (8.0x to 5.1x); cost bar still open on the packaged-chip price (31 Oct 2026)
- [Rows I and J, fair comparison and worst case](../new_start/step5_worst_case_result.md): correction of the earlier "closed"; each machine at its best batch, worst-corner failures and the levers that would fix them (31 Oct 2026)
- [Closing rows I and J](../new_start/step4_close_i_j_result.md): calibrated wafer latency model and thresholds; all pre-set bars pass on the model at central assumptions, three external numbers named (31 Oct 2026)
- [Rows I and J result](../new_start/step3_cost_power_result.md): cost per token, yield, power and heat of an SRAM wafer vs a GPU cluster and a Cerebras-class wafer; MODELLED, hinges on an assumed latency floor and system price (31 Oct 2026)
- [Rows B and A result](../new_start/step2_wafer_sram_result.md): existing models on an SRAM wafer vs a GPU cluster and a Cerebras-class wafer; capacity 2.46x (pass), energy 3.4x vs 5x bar (fail at pessimistic SRAM), MODELLED (31 Oct 2026)
- [Workload map](gpu_workload_map.md): rows A-H of what a chip must do to replace a GPU, including running existing (not only ternary) models, with mechanism, bar and status per row (31 Oct 2026)
- [GPU workload census](gpu_workload_census.md): the 19 computation patterns a GPU is used for, what version 1 tested, and how coverage would be tested (30 Oct 2026)

- [New start: target options](new_start_target_options.md): three candidate targets with reasons, first decisive tests and bars (30 Oct 2026)

- [New start charter](../new_start/README.md): clean rules, target (irregular and sparse workloads), bars and kill rules for the restarted project; [step 1 result, target 2](../new_start/step1_result.md) and [step 1 result, target 3](../new_start/step1_lm_result.md): both fail their first test (30 Oct 2026)

- [Status, 31 Oct 2026](status_31oct.md): what is measured, simulated and estimated, and what waits on whom (replaces the 28 Oct status for the current direction)

- [The founder's ternary language model project](founder_ternary_lm_context.md): why it exists, its honest results, a literature check, and the proposed joint plan with this repo (31 Oct 2026)

Related: [Home](../README.md), [Results index](../hw/results/INDEX.md)
