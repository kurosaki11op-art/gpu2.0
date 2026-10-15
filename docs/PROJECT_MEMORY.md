# SPARK: project memory (read this first)

The single place that remembers the whole project. Every session reads it first and updates it after every
experiment, decision or change of direction. The step-by-step record is `docs/journal.md`.
Last updated: 2026-10-14.

## 1. Who and what

- **Competition:** PALS innoWAH! 2026-27 pitch.
- **Team:** "L Lawliet", solo: Navin (goes by Kakashi), CKCET.
- **Repo:** `kurosaki11op-art/gpu2.0`, working branch `claude/zealous-turing-lsg561`.
- **Hardware the team owns:** Sipeed Tang Nano 20K (Gowin GW2AR-18: 20,736 LUT4, 15,552 FF, 46 x 18 Kbit block RAM
  (about 103 KB), plus 64 Mbit (8 MB) PSRAM in the package). A Windows PC with an NVIDIA GPU (runs Ollama and
  Hugging Face models; small GPU memory, so 1.5B-3B models fit and larger ones spill to CPU).
- **Project name:** SPARK. Current design: **SPARK Cortex**, a brain-principled chip that keeps learning after it ships.

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
10. The deck (`docs/SPARK_innoWAH_2026_pitch.pptx`) is **on hold**; do not update it until asked.

## 3. History: the three phases

### Phase A (9-13 Oct): SPARK v1/v2, a small brain-inspired language chip that helps a GPU
- Spiking-style recurrent byte model + recall memory, RTL, golden model, Tang Nano 20K bitstream (fits, 54 MHz),
  SKY130 ASIC flow (synthesis, OpenROAD, gate-level sim 0 mismatches, chip top with UART), KiCad boards, 3D model,
  power simulation (2.4-6.2x less energy per byte vs dense, SIMULATED), pitch deck.
- Modes tested with a GPU: answer mode, router, draft (speculative decoding) mode.
- **Key MEASURED results (real models on the user's PC):** qwen3.5:9b draft mode 1.51 tokens per big-model pass
  (lossless); answer mode safe on only ~6% of tokens; router unusable. Test 3: copy drafting 2.12, SPARK 1.58,
  multi 2.17 (9B); multi 2.28 on 3B, ~0.14 J/token ESTIMATED.
- Helper ideas tested and mostly failed: training-data filter (no gain over random), context compression (loses to
  plain), copy-failure retraining (+0.3-0.4 pt, marginal), activation-sparsity predictor (far from oracle on 3B).
- Files: `docs/spark_architecture.md`, `docs/spark_ai_development_positioning.md`, `hw/results/*` (many),
  `hw/rtl`, `hw/asic`, `hw/board`, `hw/system`.

### Phase B (12-14 Oct): matrix-free lookup core (SPARK-L)
- User asked to remove maths and matrices. Hashed lookup tables + 2-bit counters (CRC hash, XOR/shift only) matched
  the network on byte prediction; paired bootstrap: the network adds only +0.6 to +1.2 points. An earlier "network
  adds ~3 points" claim was a weak-hash artifact and was withdrawn.
- RTL: `hw/rtl/lookup/` (v1, v2 2-way + order-1 + confidence LUT, token-level core), all bit-exact (0 mismatches).
  Board top + UART host: `hw/board/lookup_board_top.v`, `host_lookup.py`; fits 54% BRAM / 13% LUT. Not yet run on
  the physical board.
- **Real-model test (MEASURED, Qwen2.5-Coder-1.5B base):** tables tie prompt lookup (code 2.41 vs 2.39, prose 2.29
  vs 2.21). **Chat model (Qwen2.5-1.5B-Instruct):** code 1.70, prose **1.04**. The prose gain was the base model
  repeating itself. Conclusion: a drafting helper cannot be the project.

### Phase C (14 Oct onward): SPARK Cortex, the redesign
- Trigger: the 1.04 result + the user's demand for something big, brain-only, provable in 6-8 months.
- Idea: today's AI is trained once and frozen; a brain keeps learning, does not forget, needs no data centre.
  SPARK Cortex keeps learning on the chip, never forgets, and chips can merge their knowledge.
- Plan and status: `docs/cortex_redesign.md`.

## 4. SPARK Cortex: how it works (current design, month 2-3, in the chip)

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
| Context memory (sim only) | hippocampal context | when known classes return under a new condition, dream a frozen copy of yesterday's counts | `cortex_int.py context=True` |

Arithmetic: compare, count, add, shift, XOR, table lookup. No multiplier, no divider, no backprop (also true in RTL).

## 5. SPARK Cortex results so far (all SIMULATED)

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
20.0 / 15.9; with replay 49.6 / 37.8 / 27.8); merge 93.0 / 82.3 / 62.6. Memory images 84 KB (137x smaller, fits block
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
5. Month 5, two boards learn separately and merge memories.
6. Month 6, sequence memory (the SPARK-L lookup core) joins for live streams.
7. Months 7-8, SKY130 area/power estimates (no fabrication), write-up, demo video, pitch. Started early: synthesis,
   placement, clock tree, global routing, clock gating; ~0.18-0.26 uJ per decision, 45-62 uJ per learned example
   (digits); detailed routing running.

Prior art: `docs/prior_art_cortex.md`. Continual-learning chips without backprop exist (HDC accelerators Clo-HDnn /
ImageHD / C-FSCIL, Intel Loihi 2); never claim "first". Measured vs HDC (`hw/results/cortex_vs_hdc.md`): chip ahead on
digits and sound, level on clothing, with less memory. Also cite WiSARD, BTHOWeN, ULEEN, Tsetlin, Numenta HTM.

Related: [Home](../README.md), [Journal](journal.md), [SPARK Cortex redesign](cortex_redesign.md),
[Results index](../hw/results/INDEX.md), [Docs index](INDEX.md)
