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

## 4. SPARK Cortex: how it works (current best design)

| Part | Brain principle | What it does | Code |
|---|---|---|---|
| Receptors | thresholds | brightness levels -> on/off bits (8 levels for sound) | `feature_layer.binarize` |
| Retina centre-surround | ganglion cells | on if brighter/darker than the 3x3 neighbour average | `binarize(('on',d))` |
| Cochlea | basilar membrane | 28 shift-add resonators, hearing-shaped bandwidths, log by leading zeros, gain control -> 28x28 sound picture | `hw/brain/cochlea.py` (`sound_picture_res`) |
| Sensory cortex | competition + Hebbian | 5x5 receptive fields, winner-take-all detectors learned without labels from stage-1 data only, 2x2 OR pooling | `feature_layer.Features` |
| Concept cells | per-class prototypes | 32 cells per class learn by counting within their class only: cannot forget, merge by pooling | `feature_layer.ConceptMemory` |
| Fast correction table | surprise / dopamine | small signed counters per (class, bit); written only when wrong or close | `sleep.SurpriseTable` |
| Sleep | hippocampal replay | concept cells dream old classes; the table practises on new data + dreams | `sleep.py`, `proof_suite_v2.py` |
| Merge | additive memories | pool two chips' concept cells, one sleep rebuilds the table | `ConceptMemory.merge` |

The chip uses compare, count, add, XOR and table lookups only. The simulator uses numpy products only as a fast way
to add table values.

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
chip model (each example seen once): all at once 96.6 / 83.7 / 71.1; 5 stages **94.6 / 78.7 / 69.7** (network 19.5 /
20.0 / 15.9; with replay 49.6 / 37.8 / 27.8); merge 93.0 / 82.3 / 62.6. Memory images 84 KB (137x smaller, fits block
RAM), sound 422 KB. Few-shot still behind the network. Known limit: dreams with independent bits cap images.

Month 3 (started early): integer model `hw/brain/cortex_int.py`; core RTL `hw/rtl/cortex/cortex_core.v` bit-exact
(0 mismatches, `run_check_cortex.py`); Tang Nano top `hw/board/cortex_board_top.v` bit-exact over UART
(`check_cortex_board.py`). **Bitstream built and timing met**: `hw/pnr_cortex/cortex_tangnano20k.fs.gz` (46/46 BSRAM,
54% LUT4, 14% FF, 0 multipliers, 68.6 MHz max at 27 MHz). Host program `hw/board/cortex_host.py` (dry run matches the
chip model exactly). Waiting on the user: program the board, run the host, measure power (month 4).
Next on our side: split dreams in PSRAM (clothing +3), feature encoder in RTL, energy estimate, seed spread.

## 6. Known failures and corrections (do not repeat)

- Weak XOR hash understated lookup tables by ~4 points; fixed with CRC. Claims corrected.
- "Network adds almost nothing" and "network adds ~3 points" both withdrawn after paired statistics.
- Base-model repetition inflated prose drafting (2.29); chat model gives 1.04.
- Random-wiring lookup neurons forget like networks under surprise learning; learned features + counting fixed it.
- Cochlea v1 (one-pole cascade) lost information (network on its pictures 54.7%); resonators fixed it (73.1%).
- Month 2: smoothing bug gave chance accuracy for homeostatic sparse cells (unseen bits got huge weights).
- Container restarts kill background jobs; launch with `run_in_background` and save logs into the repo.

## 7. Where things are

- Routine `trig_01UmL6GjCFHNfqdNTvVqZPZi`: overnight check-in every 2 h (India time); delete after 20:00 IST 15 Oct.
- **Second brain:** this repo, opened in Obsidian as a vault (Open folder as vault on `D:\gpu2.0`, Obsidian Git
  plugin to pull updates). Home: `README.md`; indexes: `docs/INDEX.md`, `hw/results/INDEX.md`, `hw/HARDWARE_INDEX.md`.
- Plan/status: `docs/cortex_redesign.md`. Journal: `docs/journal.md`. This file: `docs/PROJECT_MEMORY.md`.
- Brain core code: `hw/brain/` (`cortex_core.py` v0 random wiring, `feature_layer.py`, `sleep.py`, `cochlea.py`,
  `proof_suite.py` first proof, `proof_suite_v2.py` month 1).
- Experiment scripts and raw logs: `hw/brain/experiments/month1/`, `month2/`.
- Results: `hw/results/cortex_*.md|json`.
- Datasets (not in git, rebuilt by scripts): MNIST `mnist.npz` and Fashion-MNIST from
  storage.googleapis.com/tensorflow/tf-keras-datasets/; Speech Commands v0.01 (10 words) from
  storage.googleapis.com/download.tensorflow.org/data/. Hugging Face is blocked in the cloud container.
- Run a suite: `python hw/brain/proof_suite_v2.py DATA_DIR mnist|fashion|speech` (`COCHLEA=res` for sound).

## 8. 6-8 month plan (from `docs/cortex_redesign.md`)

1. Month 1, accuracy gap: done (simulation).
2. Month 2, shrink memory ~100x, one decision rule, few-shot: in progress.
3. Month 3, RTL bit-exact vs the Python model.
4. Month 4, Tang Nano 20K learns live over UART; power MEASURED with a USB meter.
5. Month 5, two boards learn separately and merge memories.
6. Month 6, sequence memory (the SPARK-L lookup core) joins for live streams.
7. Months 7-8, SKY130 area/power estimates (no fabrication), write-up, demo video, pitch.

Prior art: `docs/prior_art_cortex.md`. Continual-learning chips without backprop exist (HDC accelerators Clo-HDnn /
ImageHD / C-FSCIL, Intel Loihi 2); never claim "first". Measured vs HDC (`hw/results/cortex_vs_hdc.md`): chip ahead on
digits and sound, level on clothing, with less memory. Also cite WiSARD, BTHOWeN, ULEEN, Tsetlin, Numenta HTM.

Related: [Home](../README.md), [Journal](journal.md), [SPARK Cortex redesign](cortex_redesign.md),
[Results index](../hw/results/INDEX.md), [Docs index](INDEX.md)
