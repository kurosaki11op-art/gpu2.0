---
title: Docs index
tags: [spark, index]
---

# Docs index

## Now (L Cortex)

- [Project memory](PROJECT_MEMORY.md): everything in one place; read first.
- [Journal](journal.md): the step-by-step record.
- [Month 4 board plan](month4_board_plan.md): the steps that turn simulated results into MEASURED ones on the Tang Nano.
- [Overnight report, 15 Oct](overnight_report_2026-10-15.md): summary of the night's work and the board steps for today.
- [Accelerator for L, a skeptical design review](L_accelerator_design.md): profile, microarchitecture, staged path, fair comparison and risks for a dedicated chip for the L language model (a separate project from L Cortex).
- [L hypothesis, falsification and silicon plan](L_hypothesis.md): the testable hypothesis, how it can fail, node, size, material and cost (ESTIMATED).
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
- [Cortex pitch script](pitch_script_cortex.md): speaking script for the 23 Oct event, slide by slide, with a short cut list (deck: `SPARK_Cortex_pitch.pptx`).
- [Event checklist](event_checklist.md): what to do before the 23 Oct event and what to say / not say.
- [Pitch Q&A sheet](pitch_qa_sheet.md): the questions judges are likely to ask, with honest labelled answers.
- [Short paper](paper_spark_cortex.md): abstract, design, results, cost, limits and related work in two pages, for the paper-style presentation.

Related: [Home](../README.md), [Results index](../hw/results/INDEX.md)
