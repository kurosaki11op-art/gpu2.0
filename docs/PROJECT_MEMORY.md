# L: project memory (read this first)

The single place that remembers the whole project. Every session reads it first and updates it after every
experiment, decision or change of direction. The step-by-step record is `docs/journal.md`.
Last updated: 2026-10-22.

## 0. Direction change (22 Oct 2026)

- The project is renamed **L** (was SPARK). In the documents "SPARK" now reads "L"; code, board, KiCad and file names keep the `spark_` prefix so nothing breaks (for example `hw/board/spark_board_top.v`, `hw/golden/spark_golden.py`, `docs/SPARK_Cortex_pitch.pptx`, whose slides still say SPARK until the deck is rebuilt).
- Two workstreams: (1) **L Cortex**, the counting chip (everything below, 35 RTL checks pass); (2) the **L accelerator**, a dedicated chip for the L language model (attention-free, delta-rule fast weights, integer spikes, hash recall, ternary option) as the alternative to a GPU: first review in [L accelerator design](L_accelerator_design.md) (inference on the chip, training on a GPU; stage 0 = fused GPU baseline, stage 1 = bit-exact integer simulator with energy model, stage 2 = FPGA, stage 3 = silicon). Rule change for workstream 2 only: ternary add-only matrix-vector units are allowed; L Cortex keeps its brain rules. Money: the founder cannot pay for fabrication or a larger board now, so everything runs in simulation first.

## 1. Who and what

- **Competition:** PALS innoWAH! 2026-27 pitch.
- **Team:** "L Lawliet", solo: Navin (goes by Kakashi), CKCET.
- **Repo:** `kurosaki11op-art/gpu2.0`, working branch `claude/zealous-turing-lsg561`.
- **Hardware the team owns:** Sipeed Tang Nano 20K (Gowin GW2AR-18: 20,736 LUT4, 15,552 FF, 46 x 18 Kbit block RAM
  (about 103 KB), plus 64 Mbit (8 MB) PSRAM in the package). A Windows PC with an NVIDIA GPU (runs Ollama and
  Hugging Face models; small GPU memory, so 1.5B-3B models fit and larger ones spill to CPU).
- **Project name:** L. Current design: **L Cortex**, a brain-principled chip that keeps learning after it ships.

## 2. Standing rules from the user (never break these)

1. **Honest labels on every number:** MEASURED (real hardware or real model), SIMULATED (our simulator),
   ESTIMATED (arithmetic on stated assumptions), PROJECTED (needs silicon or a bigger test). Say when something failed.
2. **Identity is "a human brain as a chip".** Follow brain principles only. No heavy maths, no matrices, no
   multiplies, no backprop in the chip. Lightweight, efficient, effective, better than today.
3. **Do not pivot to "FPGA builder" or helper framing.** A chip that only helps a GPU on ~6% of work was rejected:
   "go for something big".
4. **Short horizon:** a provable result within 6-8 months. Nothing that needs 10-15 years. No fabrication yet
   (especially not 130 nm). Shrink first, prove the concept, attract investors.
5. **Scope:** efficiency, effectiveness, e-waste, training cost, memory/weight transfer, AI advancement.
   "Do anything as you wish but don't go away from the scope."
6. **Never forget the project:** write everything to markdown in GitHub, every step (this file + journal + logs).
   The repo is the second brain, read in Obsidian; keep every note linked from an index.
   Commit and push after every experiment. The stop hook also requires a clean tree.
7. **Never put AI model identifiers in repo content** (commits, docs, code comments).
8. **Commit trailer:** `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and
   `Claude-Session: https://claude.ai/code/session_014mQCCzGRbma37WnmMzZ7Xo`. Push only to the working branch.
   No pull request unless asked.
9. The user runs real-model tests on their PC. Point their downloads and models to the **D: drive**, not C:
   (`HF_HOME=D:\hf_cache`). Cloud work happens in the session container and never touches their PC.
10. **Event on 23 Oct 2026** (user will present; "pitch / project / paper presentation"). The old GPU-helper deck (`docs/SPARK_innoWAH_2026_pitch.pptx`) is superseded by the Cortex deck `docs/SPARK_Cortex_pitch.pptx` (13 slides, speaker notes; script `docs/pitch_script_cortex.md`, Q&A `docs/pitch_qa_sheet.md`, short paper `docs/paper_spark_cortex.md`). The hold is lifted (18 Oct); keep these in step with `docs/results_at_a_glance.md` and the claims sheet.

11. **Strict brain principles in every process (21 Oct).** Each process must pass the six-point test in
    `docs/brain_principles_audit.md` (local rule, no outside conductor, few labels, one pass with no stored data, innate or
    locally learned sensing, cheap and sparse). Never describe the chip as "learning like a brain" beyond what the audit allows.

12. **No-regression rule (20 Oct night, user).** A change counts as a fix only if, against the shipped settings (margin 256 / 1,500 dreams / 1 night), it passes all three at once, 3 seeds, SIMULATED: digits staged >= 95.5, clothing staged >= 83.3, words (20) clean >= 73.3 with oldest words not lower. Anything that gains on one and loses on another is recorded as a failure (or as a trade-off) and stays a side experiment; do not merge it. A per-dataset switch is allowed only if the chip can decide it from its own signals (for example its surprise rate). Window of failed or traded-off ideas so far: fine code, hard-example replay, cut-and-paste dreams, delay-line cells (see `docs/journal.md`, 20 Oct night).

## 3. History: the three phases

### Phase A (9-13 Oct): L v1/v2, a small brain-inspired language chip that helps a GPU
- Spiking-style recurrent byte model + recall memory, RTL, golden model, Tang Nano 20K bitstream (fits, 54 MHz),
  SKY130 ASIC flow (synthesis, OpenROAD, gate-level sim 0 mismatches, chip top with UART), KiCad boards, 3D model,
  power simulation (2.4-6.2x less energy per byte vs dense, SIMULATED), pitch deck.
- Modes tested with a GPU: answer mode, router, draft (speculative decoding) mode.
- **Key MEASURED results (real models on the user's PC):** qwen3.5:9b draft mode 1.51 tokens per big-model pass
  (lossless); answer mode safe on only ~6% of tokens; router unusable. Test 3: copy drafting 2.12, L 1.58,
  multi 2.17 (9B); multi 2.28 on 3B, ~0.14 J/token ESTIMATED.
- Helper ideas tested and mostly failed: training-data filter (no gain over random), context compression (loses to
  plain), copy-failure retraining (+0.3-0.4 pt, marginal), activation-sparsity predictor (far from oracle on 3B).
- Files: `docs/spark_architecture.md`, `docs/spark_ai_development_positioning.md`, `hw/results/*` (many),
  `hw/rtl`, `hw/asic`, `hw/board`, `hw/system`.

### Phase B (12-14 Oct): matrix-free lookup core (L-lookup)
- User asked to remove maths and matrices. Hashed lookup tables + 2-bit counters (CRC hash, XOR/shift only) matched
  the network on byte prediction; paired bootstrap: the network adds only +0.6 to +1.2 points. An earlier "network
  adds ~3 points" claim was a weak-hash artifact and was withdrawn.
- RTL: `hw/rtl/lookup/` (v1, v2 2-way + order-1 + confidence LUT, token-level core), all bit-exact (0 mismatches).
  Board top + UART host: `hw/board/lookup_board_top.v`, `host_lookup.py`; fits 54% BRAM / 13% LUT. Not yet run on
  the physical board.
- **Real-model test (MEASURED, Qwen2.5-Coder-1.5B base):** tables tie prompt lookup (code 2.41 vs 2.39, prose 2.29
  vs 2.21). **Chat model (Qwen2.5-1.5B-Instruct):** code 1.70, prose **1.04**. The prose gain was the base model
  repeating itself. Conclusion: a drafting helper cannot be the project.

### Phase C (14 Oct onward): L Cortex, the redesign
- Trigger: the 1.04 result + the user's demand for something big, brain-only, provable in 6-8 months.
- Idea: today's AI is trained once and frozen; a brain keeps learning, does not forget, needs no data centre.
  L Cortex keeps learning on the chip, never forgets, and chips can merge their knowledge.
- Plan and status: `docs/cortex_redesign.md`.

## 4. L Cortex: how it works (current design, month 2-3, in the chip)

| Part | Brain principle | What it does | Code / RTL |
|---|---|---|---|
| Receptors | thresholds | brightness > 50 and > 150 -> on/off bits (sound: 8 levels) | `feature_layer.binarize`, `cortex_encoder.v` |
| Retina centre-surround | ganglion cells | ON/OFF if brighter/darker than the 3x3 neighbour average by > 8 | same |
| Cochlea (sound) | basilar membrane, adaptation | 28 shift-add resonators -> frame sums -> per-resonator noise floor (4x mean of the 4 quietest frames) -> 28x28 sound picture | `hw/brain/cochlea_int.py`, `cortex_cochlea.v` (bit-exact) |
| Sensory cortex | competition, Hebbian | 5x5 windows, 32 label-free detectors per channel (winner by XNOR + bit count), 2x2 pooling -> 4,608-bit code | `Features` / `cortex_encoder.v` (detectors loaded, or learned on chip with the `ENC_LEARN` build: bit-exact with `detector_learn.py`, 94.5 / 80.0 vs PC 95.0 / 79.2; ASIC only) |
| Fast table | surprise / dopamine | 5-bit signed counters per (class, bit); decides everything; written only when wrong or close | `cortex_core.v` |
| Dream memory | synaptic scaling | 10-bit per-class on-counts per bit, halved when the class count fills | `cortex_core.v` |
| Day | replay, daydreaming | each example once: count, practise, one daydream; dreams of old classes interleaved | host schedule / `cortex_int._stage` |
| Night | sleep | dreams of all known classes, up to 2 passes; ends itself after 256 dreams with > 2 surprises | same |
| Dreams | generative replay | per bit: xorshift random draw below the class count (redraw if too big), on if below the bit's count | `cortex_core.v` |
| Memory transfer | additive memories | export / import words; merge = add tables (saturate) and counts (halve when full), then one night | `cortex_core.v` op 7, `cortex_host.merge` |
| Slow table (ASIC option, 18 Oct) | cortical consolidation | a second 8-bit table follows the fast one (S += ((W<<3) - S + 16) >> 5 every 500 ticks); prediction reads it; all-at-once clothing 83.4 -> 87.6, words 83.1 -> 86.4, digits 97.0 -> 97.8; staged clothing 78.4 -> 81.6 (slow consolidation damps the recency bias) | `cortex_core.v` option `CORTEX_SLOW`, `hw/brain/cortex_slow.py` |
| Embedding path (ASIC option, 20 Oct) | relational coding (familiarity profile) | a new word is a prototype in the space of the table's scores over ~15 known words (L1 nearest prototype; old words get K=3 competitive prototypes; new words a running mean of 1-5 clips); the table is untouched | `cortex_core.v` option `CORTEX_EMBED`, `hw/brain/cortex_embed.py` |
| Context memory (sim only) | hippocampal context | when known classes return under a new condition, dream a frozen copy of yesterday's counts | `cortex_int.py context=True` |

Arithmetic: compare, count, add, shift, XOR, table lookup. No multiplier, no divider, no backprop (also true in RTL).

## 5. L Cortex results so far (all SIMULATED)

First proof (`hw/results/cortex_proof.md`): learning in 5 stages, digits 95.6% vs network 19.5% (replay 51.6%);
exact merge; few-shot worse than the network.

Month 1 (`hw/results/cortex_month1.md`):

| | Digits | Clothing | Spoken words |
|---|---|---|---|
| Network, all data at once | 97.7 | 87.4 | 75.5 (our pictures) / 76.2 (FFT log-mel) |
| Brain best part, all at once | 97.9 (combined) | 85.8 (table) | 76.1 (table) |
| Network, 5 stages | 19.5 | 20.0 | 15.9 |
| Brain best part, 5 stages | 97.2 (concept) | 86.3 (combined) | 71.8 (table) |
| Merge, chips knew different classes | 97.2 | 84.6 | 66.2 |

Open after month 1: memory 11-28 MB (too big), no single decision rule, few-shot not re-tested.

Month 2 (`hw/results/cortex_month2.md`, closed): 5-bit fast table decides everything (one rule); dream memory =
10-bit per-class counters with synaptic scaling; day = count + practise + daydream + interleaved dreams of old classes;
night = dreams of all classes that **ends itself** after a block of 256 dreams with >2 surprises. On the exact integer
chip model (each example seen once): all at once 96.6 / 83.7 / 71.1 (seed means, 15 Oct: 96.9 / 82.9 / 71.9 - clothing varies 82.2-83.7 with example order); 5 stages **94.6 / 78.7 / 69.7** (network 19.5 /
20.0 / 15.9; with replay 49.6 / 37.8 / 27.8); merge 93.0 / 82.3 / 62.6 (3-seed means 15 Oct: 93.3 / 81.4 / 64.3; hand-over - A's memory copied into B, which then learns its own classes - 95.6 / 82.7 / 71.6, see `hw/brain/experiments/month4/merge_variants.md`). Memory images 84 KB (137x smaller, fits block
RAM), sound 422 KB. Few-shot still behind the network. Known limit: dreams with independent bits cap images.

Month 3 (done early, `hw/results/cortex_month3.md`): integer chip model `hw/brain/cortex_int.py`; core
`hw/rtl/cortex/cortex_core.v`, sensory encoder `cortex_encoder.v`, Tang Nano top `hw/board/cortex_board_top.v` - all
bit-exact (0 mismatches; core also with the SKY130 SRAM models). **Bitstream** `hw/pnr_cortex/cortex_tangnano20k.fs.gz`:
raw images in, learning, dreaming, memory export/import; 46/46 BSRAM, 89% LUT4, 0 multipliers, 69.8 MHz max at 27 MHz; dream batches (command 45).
Host `hw/board/cortex_host.py` (+ `--onchip-encode`), transfer demo `cortex_transfer.py` (91.4% after merging two
halves), live demo `cortex_demo.py`. Extra evidence: 10 one-class stages 93.0 / 78.7 / 71.2 (3 seeds; sound with the chip cochlea + noise floor) (network ~10%); vs HDC
ahead on digits and sound, level on clothing; energy ~74x per decision, ~200x per learned example (ESTIMATED); ASIC
SKY130 ~18.8 mm2 (17.9 of it open SRAM macros; logic < 1 mm2); after placement + global routing ~42-43 MHz; power 355 mW without clock gating
(SRAM macros clocked every cycle), 35-49 mW with per-memory clock gating (130 gates), a lighter clock tree and the pipelined core (`CORTEX_PIPE`,
264 cycles per decision; all bit-exact): ~0.18-0.26 uJ per decision - still ~20-28x above the operation-count energy, so the 74x is per operation needed, not
per chip (`hw/results/cortex_asic_estimate.md`). On-chip detector learning: in RTL (`ENC_LEARN`, bit-exact),
one pass over the first day's images: digits 94.5 / clothing 80.0 vs PC detectors 95.0 / 79.2 (SIMULATED). Sound chip: live sound -> streaming cochlea (noise floor) -> general encoder -> core, whole chain bit-exact in RTL (`hw/results/cortex_sound_chip.md`); sound 71.2 (5 seeds). Rejected: second sensory layer (V2), wider pooling
for few-shot. Waiting on the user: run on the board, measure power (month 4).

Limit found 15 Oct: "never forgets" holds for new classes, NOT for a new condition of known classes (domain shift);
fix = frozen copy of the dream counts (2x dream memory), in the RTL as build option `CORTEX_CONTEXT` (bit-exact,
ASIC only; `hw/results/cortex_new_condition.md`).

Month 4 work while waiting for the board (15 Oct, `hw/brain/experiments/month4/`, one page:
`docs/results_at_a_glance.md`):
- Sound: per-resonator **noise floor** in the cochlea, 69.6 -> 71.2 (5 seeds); all at once 71.9 = 5 stages 72.0;
  vs HDC on the same codes +5.7. **Sound on today's Tang Nano bitstream** (PC cochlea -> sound picture -> image chip):
  60.1 (`cortex_host.py --task sound`, board plan step 9); live sound demo `cortex_sound_demo.py` (a new word needs
  many repetitions: 44% from 60 clips).
- Energy (ESTIMATED, SKY130 layout): 0.19-0.26 uJ per decision, 45-62 uJ per learned example (digits, ~95% dreams);
  economy dream budget (`--economy`): ~3x less for -0.6 to -0.8 points.
- Noise (user: remove the noise that affects accuracy): the 4x noise floor is the best filter (trained clean, at 5 dB
  SNR 46.6 vs 32.1 without); gates and smoothing do not help; learning from noisy examples adds +5 to +11 in noise for
  3-5 points clean (`hw/brain/experiments/month4/input_noise.md`).
- Rejected / within noise: few-shot saccades and replay (top-2 voting small gain), lateral inhibition in the cochlea,
  retinal adaptation for images; ASIC option: 3 brightness receptors (+0.8 clothing, +25% memory).
- ASIC detailed routing did not converge (two floorplans, lost in container restarts) - parked.
- All 14 bit-exact checks pass: `sh hw/run_all_checks.sh DATA_DIR` (`hw/check_summary.txt`). Board preflight:
  `hw/board/preflight.py`.

Month 4, 18-19 Oct (`hw/brain/experiments/month4/slow_table_and_staged_limits.md`): **what limits the scores.** The chip's own code is not the limit (a floating-point linear readout on it reaches 87.9% clothing / 98.3% digits);
the online 5-bit readout is. Slow table (Redesign 6, RTL option `CORTEX_SLOW`, K = 5, bit-exact): all at once clothing 88.3, words 87.5, digits 98.4 (5 seeds, LOOK AGAIN; level with a small MLP, not better); staged clothing 81.6 (was 78.4).
Staged learning is limited by dream fidelity (recency bias: last-stage classes absorb older ones, 7 -> 9 +21 points); cheap fixes failed (more daydreams, margins, group-structured dreams, bias rules, dream margin);
only prototype dreams help (K = 4 + slow table: clothing 80.7, 4x dream memory). Rejected: pool-limited prototypes, rectangular sound detectors, exemplar memory for new words (the word limit is the features, needs more speech data).
Pitch material for the 23 Oct event: `docs/SPARK_Cortex_pitch.pptx`, `pitch_script_cortex.md`, `pitch_qa_sheet.md`, `paper_spark_cortex.md` (deck to be refreshed with the slow-table numbers).

New spoken words (20 Oct, `hw/brain/experiments/month4/multiproto_dreams.md` sections 9-12): errors follow twin words (no/go, left/right), not learning order; fitting detectors on more words does not help, more known classes in the table hurt; a GPU-style CNN beats the chip (63.7 vs 51.5 at 5 recordings); the table-score embedding path (RTL option CORTEX_EMBED, bit-exact) reaches 50.2 / 56.4 / 62.3 (all ten words) at 1 / 2 / 5 recordings with old words unchanged; finer sound grid 3,3,1,1,4,4 gives new words 32.3 vs 18.5 in the table path (full check pending).

## 6. Known failures and corrections (do not repeat)

- Weak XOR hash understated lookup tables by ~4 points; fixed with CRC. Claims corrected.
- "Network adds almost nothing" and "network adds ~3 points" both withdrawn after paired statistics.
- Base-model repetition inflated prose drafting (2.29); chat model gives 1.04.
- Random-wiring lookup neurons forget like networks under surprise learning; learned features + counting fixed it.
- Cochlea v1 (one-pole cascade) lost information (network on its pictures 54.7%); resonators fixed it (73.1%).
- Month 2: smoothing bug gave chance accuracy for homeostatic sparse cells (unseen bits got huge weights).
- Container restarts kill background jobs; launch with `run_in_background` and save logs into the repo.
- 15 Oct: wrote that the SRAM macros were missing from the layout power; wrong (they were 72% of it). Corrected.
- 15 Oct: two RTL checks in one folder at once overwrite each other's files and give false mismatches (never again).
- 15 Oct: the first dream-batch bitstream and the pipelined core did not fit the Tang Nano (94-101% LUT4); fixed by
  packing the encoder's code map; the pipelined core is ASIC-only (`CORTEX_PIPE`).
- 15 Oct: check scripts captured the SRAM models' per-access output in memory (out-of-memory kill); now filtered.

## 7. Where things are

- Routine `trig_01UmL6GjCFHNfqdNTvVqZPZi`: overnight check-in every 2 h (India time); delete after 20:00 IST 15 Oct.
- **Second brain:** this repo, opened in Obsidian as a vault (Open folder as vault on `D:\gpu2.0`, Obsidian Git
  plugin to pull updates). Home: `README.md`; indexes: `docs/INDEX.md`, `hw/results/INDEX.md`, `hw/HARDWARE_INDEX.md`.
- Plan/status: `docs/cortex_redesign.md`. Journal: `docs/journal.md`. This file: `docs/PROJECT_MEMORY.md`.
- Brain core code: `hw/brain/` (`cortex_core.py` v0 random wiring, `feature_layer.py`, `sleep.py`, `cochlea.py`,
  `proof_suite.py` first proof, `proof_suite_v2.py` month 1).
- Experiment scripts and raw logs: `hw/brain/experiments/month1/` to `month4/`.
- RTL: `hw/rtl/cortex/` (core, encoder, checks); board: `hw/board/`; FPGA build: `hw/pnr_cortex/`; ASIC estimate
  flow and logs: `hw/asic/cortex/` (`flow.tcl`, `power_gated.tcl`, `route.tcl`, run folders `ungated/`, `gated_enc/`,
  `gated_all/`, `cts_light/`, `pipe_light/`).
- Results: `hw/results/cortex_*.md|json`.
- Datasets (not in git, rebuilt by scripts): MNIST `mnist.npz` and Fashion-MNIST from
  storage.googleapis.com/tensorflow/tf-keras-datasets/; Speech Commands v0.01 (10 words) from
  storage.googleapis.com/download.tensorflow.org/data/. Hugging Face is blocked in the cloud container.
- Run a suite: `python hw/brain/proof_suite_v2.py DATA_DIR mnist|fashion|speech` (`COCHLEA=res` for sound).

## 8. 6-8 month plan (from `docs/cortex_redesign.md`)

1. Month 1, accuracy gap: done (simulation).
2. Month 2, shrink memory ~100x, one decision rule: done; few-shot: narrowed, still behind a network at 5 examples.
3. Month 3, RTL bit-exact vs the Python model: done (core, encoder, board, memory transfer, dream batches; build
   options `ENC_LEARN` on-chip senses, `CORTEX_CONTEXT` context memory, `CORTEX_PIPE` pipelined core).
4. Month 4, Tang Nano 20K learns live over UART; power MEASURED with a USB meter: **waiting on the user's board**
   (`docs/month4_board_plan.md`).
4b. Final numbers 16 Oct (SIMULATED, 5 seeds, margin 32 + word alignment + LOOK AGAIN; all at once / 5 stages): digits
   98.0 / 95.8, clothing 84.8 / 78.3, words 84.7 / 82.9 (`hw/brain/experiments/month4/final_numbers.py`); regression
   18/18. Done 15 Oct (SIMULATED, in RTL): word alignment for sound (~72 -> 82.5 all at once); IMPRINT + short sleep for a
   new class from a few examples (digits 1 example 54.1 -> 69.9, clothing 49.7 -> 64.0); see
   `hw/brain/experiments/month4/fewshot_imprint.md`. Board testing set aside by the user.
5. Month 5, two boards learn separately and merge memories; also try the hand-over (`cortex_transfer.py --handover`), which beats the merge in simulation (+7.3 on sound).
6. Month 6, sequence memory (the L lookup core) joins for live streams.
7. Months 7-8, SKY130 area/power estimates (no fabrication), write-up, demo video, pitch. Started early: synthesis,
   placement, clock tree, global routing, clock gating; ~0.18-0.26 uJ per decision, 45-62 uJ per learned example
   (digits); detailed routing: converged 16 Oct to **1 violation** (from 174,309) after spreading the cells (placement density 0.15) and moving the met5 power stripes away from the SRAM macro edges; see `hw/results/cortex_asic_estimate.md`.

Prior art: `docs/prior_art_cortex.md`. Continual-learning chips without backprop exist (HDC accelerators Clo-HDnn /
ImageHD / C-FSCIL, Intel Loihi 2); never claim "first". Measured vs HDC (`hw/results/cortex_vs_hdc.md`): chip ahead on
digits and sound, level on clothing, with less memory. Also cite WiSARD, BTHOWeN, ULEEN, Tsetlin, Numenta HTM.

## Brain-strict redesign (19 Oct 2026, SIMULATED)

Rule 11 and the audit in `docs/brain_principles_audit.md`; results in `hw/results/brain_strict_redesign.md`. Working: on-chip detectors (digits 94.1), sleep from inside (digits 94.1-94.7), few-label learning with context-limited self-labelling
(digits 10 / 5 / 2 % labelled 93.1 / 91.3 / 90.7 vs 94.1; clothing about 78 vs 80.8), pruning (19-30 % of synapses kept for 0-0.5 point; saving ESTIMATED). Also: eye movements (5 shifted views) with agreement gating: few labels digits 2 % 93.9 vs 94.1 full, and every label present digits 94.9 vs 94.1 (not on clothing). Failed: all-class self-labelling, scattered rewards, unsupervised category layer, cascade synapses,
dreams with lateral inhibition, fixed-loudness onset. Also: stages blended in one stream with context taken from recent rewards, no stage boundaries: digits 10 % labelled 92.7-93.1 vs 94.6 control. Sound: causal onset trigger near parity with the shipped alignment only with look-again (clean 66.3 vs 69.2), noisy dreams within noise (not adopted). Open: novelty from inside, a temporal layer for twin words, correlated dreams, a larger test to settle the onset trigger, RTL for the new host-level logic.

## Recommended chip settings (19 Oct 2026, SIMULATED, 3 seeds)

Update margin **256** (core parameter `MARGIN`, was 32), **1,500** dreams per old class per stage (was 6,000), **1** night pass (was 2). Staged / all at once, shipped settings -> new: digits 94.1 / 97.0 -> 95.5 / 97.5; clothing 80.8 / 86.0 -> 83.3 / 86.55 (stride-1 encoder 83.65 / 87.2); spoken words clean 68.5 -> 73.35, last-stage words 50.6 -> 57.1.
No extra memory; RTL bit-exact at margin 256 (`run_check_cortex_hooks.py --margin=256`). Also in the overnight round: noisy-copy training lifts clean and noise accuracy (words clean 69.2 -> 73.3, 5 dB 33.5 -> 56.4; control pending), the stride-1 encoder lifts all-at-once on both image sets, RTL hooks (`CORTEX_HOOKS`: top margin, write counter) are bit-exact.

## Staged learning and efficiency findings (20 Oct 2026 night, SIMULATED)

Isolation: blocked classes with no dreams 44.8 clothing, shipped staged 83.3, replaying all earlier real data 87.1: the staged loss (clothing 3.8, digits 1.6) is replay fidelity. Failed: prioritised replay, graded surprise, budget, night downscaling, cut-and-paste dreams, detector coverage, reward-gated detectors, graded code, second layer, fovea. Traded off: fine code (one-pass 88.1 / 98.0, staged lower), hard-example replay (clothing +1.2, digits -0.4 to -1.0), coincidence cells (twin +4.8, old words -1.7). Wins: Module 2 sleep category formation for few labels (digits 5 % labels 89.9 -> 91-94), timing cells (twin +4.8), early exit (clothing reads 58 % of the active bits, digits 29 %, at -0.05 / -0.4 accuracy). The single-layer code saturates near 88 for clothing (kernel readout 88.35).

## Kept: measured GPU comparison and two-sense learning (20 Oct 2026 night, SIMULATED unless MEASURED)

Same-data reference (MEASURED, a small CNN trained on the same 10,000 / 2,000 images; a ruler only, never in the chip): clothing joint 88.8 vs L one-pass 86.55; digits 98.55 vs 97.47; 20 words 77.05 vs 73.35 (staged). Staged, the CNN collapses (about 20 % without help; with 160 stored images 28-32 %; it needs about 4,000 stored images, 24x the chip's memory, to reach 87.8 / 95.9 vs L 83.3 / 95.5 with no stored data). Twin words are NOT a special gap (corrected 20 Oct night: the 20-word set has only 4 twin words; on 35 words L's float readout 68.6 vs CNN 65.4 on twin words); the real word gap is the staged loss (chip 73.35 / 68.3 vs its float readout 79.95 / 73.8).
Two senses (kept as a separate capability, no change to the baselines): picture + sound in one table 98.33 vs 97.40 picture alone; a damaged picture is covered by sound (97.28 vs 85.4); with ZERO picture labels, names from an ear that is right on 73.5 % of unfamiliar speakers give 89.7, and sleep-time neighbour cleaning lifts that to 93.9 (true labels 97.40). Cost: the sound code adds 23,040 bits to the table. Scripts `brain_strict_twosense.py`, `brain_strict_twosense2.py`; data: FSDD downloaded with `fsdd_prep.py`.

Hard-example replay (20 Oct night, SIMULATED): NOT adopted. Its apparent +1.0 on clothing came from nights cut short by the stop rule; with consolidation made reliable clothing is 82.4 vs 83.2 shipped (digits +0.7, words +1.8 stay). Learned: the night's job is letting the slow table follow the fast one; dream replays almost never write; with about 1,000 stored traces per class staged equals one-pass (about 4 MB).

## Sensory node (20 Oct 2026 night, built and checked)

Two senses in one chip: `rtl/cortex/cortex_sense_top.v` (retina 4 x 32 + cochlea with a 4 x 32 sound encoder, one core NB = 9,216, AW = 14), `cortex_neighbours.v` (sleep neighbours), core `rd_scores`; host pooling `hw/brain/cross_modal.py`. All bit-exact (`run_check_sense_top.py`, `run_check_neighbours.py`, `run_check_sleep_clean.py`, `run_check_cortex_twosense.py`, hooks check with score lines), in `hw/run_all_checks.sh`. Results and limits: [sensory node](../hw/results/sensory_node.md). Wording rule: say "no stored examples" (the table and the dream counts are stored), never "no weights" or "no stored data".
Weak-spot round (20 Oct night, SIMULATED unless marked): A the two-sense result holds on a second pair (MNIST + Speech Commands digits: zero picture labels 92.3 -> 96.9 after cleaning vs 97.4 labelled); B clothing with a simulated name source 60-73 % right reaches 85.2-85.4 after cleaning vs 86.55 labelled; C F1 settled by design (alignment inside a one-second echoic buffer; a fully streaming trigger stays about 3 points worse at 35 words); D two senses raise staged digit accuracy by +1.1 to +2.2, the clothing staged floor (83-84 vs 86.55 one pass) stays; E new spoken words from 1-5 recordings are within about 2-5 points of a GPU-style model (50.2 / 56.4 / 62.3 vs 55.1 / 63.7), limited by the small vocabulary. F5 (staged loss) root cause found (20 Oct night): per-bit dream counts give typical samples; the old-vs-new boundary is set by the TAILS of the classes, which the dream memory does not encode; dream reshaping (about 15 variants including boundary dreams) cannot add them; only real tail data (about 4 MB for full recovery), a second sense (digits +1.1 to +2.2) or a second look (+0.45) help. F10 improved (ASIC option, SIMULATED, not in RTL): a second table on the finer code consulted only for the 20 % least-sure inputs (share from the unlabelled margin distribution) gives clothing 88.03 one pass (coarse 86.55, CNN 88.8 MEASURED), digits 98.10 (97.47; CNN 98.55), staged clothing 83.72 (83.27), digits staged unchanged, for +41 % reads and about 2.8x the memory. F9 improved: new words learned through the pictures seen with them reach 56.4 / 71.3 from sound alone against 10.1 / 33.6 with 5 recordings. F7 (noticing a new class by itself) WORKS with two senses: novelty AUROC 0.96 / 0.97, flagged pairs 99 % really new, the new digits learned in one stage (all 10 digits 93.7 / 97.3 vs oracle 96.8 / 97.6, old digits not forgotten); picture bits alone cannot do it (AUROC 0.53-0.57). F3 (unsupervised category layer) WORKS with two senses: 30 label-free groups from co-occurring pictures and sounds, one label per group (30 labels in total), refined in sleep: picture learner 96.1 / 97.0 vs 97.4 with all 10,000 labels (picture-only groups never passed about 67). Details in `docs/journal.md` (20 Oct night) and [sensory node](../hw/results/sensory_node.md). F5 PARTLY BROKEN (21 Oct, SIMULATED): surprise-tagged TAIL MEMORY (rule `tailmem`, 3/16 of dreams from a second count memory updated only on table writes, +57 KB) gives staged clothing 83.18 -> 84.52, digits 94.87 -> 95.90 (5 seeds), words 73.35 -> 74.15 (20, oldest 77.5 -> 81.8) and 68.29 -> 68.53 (35; newest -3.8); passes rule 12; one pass unchanged; not in RTL. SECOND LOOK ON WORDS (21 Oct, SIMULATED, staged, 3 seeds): second table on a finer sound code (3x3 windows, stride 1, pool 3x3) consulted for the 20-40 % least-sure clips: 20 words 73.35 -> 75.44-75.93 (oldest 77.5 -> 80.5), 35 words 68.29 -> 70.66-70.71; ~2x sound memory, ASIC option, not in RTL; stacking it with the tail memory is NOT additive (20 words 75.04 < 75.93), so pick one per product. CUE WEIGHTING across senses (shifts only, two tables, same memory): clean 98.33 -> 98.87, picture 25 % damaged 97.45 -> 98.40, sound 50 % damaged 98.60 -> 98.85 vs plain sum 99.20; not in RTL. PLAN RESULT (21 Oct): (1) DONE: tail memory in the core (op 0 TAILCOUNT, frozen memory reused, CLEAR zeroes it; bit-exact at 4 counter widths, also pipelined), cue-weighting unit `cortex_cue.v` (bit-exact, 1,200 cases) and second-look unit `cortex_look.v` plus a two-core integration check, all in `hw/run_all_checks.sh` (35 checks; 35/35 passed in one full rerun); (2) digits one-pass gap: LIMIT, second look plateaus at 98.10 (CNN 98.55); (3) readout precision: no gain, 5-bit is the sweet spot, the 1-2 point gap to a float readout is not about count range. WORDS (21 Oct): noisy-copy training (one noisy copy of every clip per stage, no extra memory) lifts 5 dB from 39.5 to 59.0 (20 words) and 27.4 to 42.8 (35 words); stacked with the second look: 20 words 75.68 clean / 61.9 at 5 dB, 35 words 72.43 clean (CNN ruler about 72.5) / 47.2 at 5 dB; passes rule 12; remaining word gap: 1.4 points at 20 words. SCALE (22 Oct): at 60,000 training images one pass 87.31 clothing / 97.88 digits but STAGED falls to 77.98 / 93.42 (10,000 images: 83.27 / 95.52); dreams, counter width and margin settings do not fix it; staged claims are for 2,000-image stages. Environment note: the cloud container is reclaimed while the session is idle, so long checks must run inside an active turn.

## Start here for a fresh session (21 Oct 2026)

- Data folders live in a session scratchpad and are NOT in the repo: MNIST / Fashion / speech frame sums (`speech_framesums_int.npz`), `fsdd_framesums_int.npz` (made by `hw/brain/experiments/month4/fsdd_prep.py`, source raw.githubusercontent.com), `word_codes_*.npz` (made by `save_word_codes.py` / `save_word_codes_geom.py DATA 3,3,1,1,4,4,64 geom3311`). A new session must re-fetch them; the original speech source host was `download.tensorflow.org` (blocked unless added under Allowed domains, applies to new sessions).
- Open work: larger base vocabulary for new spoken words (needs the bigger speech set; 1-shot new words ~15 %, 5-shot 44.7 %, SIMULATED); embedding path with the finer sound grid through the RTL; finer-grid noise check; re-run `hw/run_all_checks.sh` (expect 24 checks); floor2g routing result (met1-met4 attempt; run `diag/drc_summary.py`, not recorded yet); board day on the user's PC.

Related: [Home](../README.md), [Journal](journal.md), [L Cortex redesign](cortex_redesign.md),
[Results index](../hw/results/INDEX.md), [Docs index](INDEX.md)
