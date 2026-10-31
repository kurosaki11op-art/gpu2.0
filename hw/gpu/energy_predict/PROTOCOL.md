---
title: Test G1 protocol - predict decode speed and energy per token on other people's GPUs, then measure (31 Oct 2026, pre-registered)
tags: [spark, gpu, wedge, energy, measurement, protocol, vision-research]
---

# Test G1: predict, then measure (pre-registered 31 Oct 2026)

Why: [Vision research 01](../../../docs/reviews/research_01_summary.md), gap G1 and wedge 1 (an independent cost and energy planner). Question: can a simple memory-bound model, fitted on one GPU, predict speed and energy per token on a different GPU, and is that useful to the people who own them. Labels: predictions MODELLED; results MEASURED once run (board power as reported by `nvidia-smi`, not wall power).

## Who and what

- Reference GPU: the founder's RTX 3050. Targets: the friends' RTX 3050 (4 GB and 6 GB versions) and the 4060 (6 GB), each possibly a laptop part. Names and exact variants are recorded from the tool's output.
- Models: three decoder language models of increasing size that fit in 4 GB in half precision with the cache: roughly 0.1 billion, 0.5 billion and 1 billion parameters (the founder chooses public checkpoints and records them in the results). Same three on every machine.
- Batch sizes 1, 4, 16; prompt 256 tokens; 128 new tokens. 3 models x 3 batches = **9 points per GPU**.

## Steps (order matters)

1. **Founder, reference GPU:** `python measure.py MODEL --out ref_MODEL.json` for the three models; `python predict.py fit ref_*.json --out fit.json`. Commit `fit.json` and the three result files.
2. **Friends, before any model is run:** `python measure.py x --info-only --out info_NAME.json` (30 seconds of idle power plus a bandwidth test). Send the file. The founder runs `predict.py predict` for each friend and each model and **commits the predictions** (`predictions_NAME_MODEL.json`) before the friends run the models.
3. **Friends:** run `measure.py` for the three models and send the JSON files. Commit them unedited.
4. **Compare** prediction with measurement per point. Report every point, including misses.

## Bars (fixed now; not changed after the runs)

- **G1-speed:** tokens per second per user predicted within 20% of measured, on at least 7 of the 9 points on each target GPU.
- **G1-energy:** joules per token (gross, board power) predicted within 20%, on at least 7 of 9 points on each target GPU. Expected to be the harder one (power depends on the GPU's own limits); a miss is a finding.
- If a laptop does not report power, only G1-speed applies to it.
- Points where the model does not fit in memory are excluded and listed.
- **Kill rule for wedge 1** (Vision's bar): if the speed or energy prediction fails on most target GPUs, withdraw the planner idea as stated and record why. **Demand test, separate:** ask each friend whether this answered a question they had; the real demand bar is 2 of 10 buyers asking for it, which four friends cannot meet.

## Amendment 1 (31 Oct 2026, after the reference GPU was measured, before any other GPU): the predictor rule failed on its own data

The reference GPU (founder's RTX 3050 6 GB laptop; results in [`results_3050/`](results_3050/)) was measured first. Rule v1 (bytes over bandwidth) fitted that data badly: **1 of 9 points within 20% in-sample** ([table](results_3050/v1_in_sample.txt)). Per-layer time was almost constant (about 1.0 to 1.2 ms) over a 14x range of model size, so on this software stack decode speed is set by per-layer launch overhead on the CPU side, not by memory bandwidth. **Rule v1 is recorded as failed in-sample; it is not rescued.**

Rule v2 (in [`predict.py`](predict.py), `fit2` and `predict2`): step time = layers x g + bytes x a + 2 x parameters x batch x e, with g scaled by a measured launch cost per tiny operation on the target machine, a by copy bandwidth and e by a measured matrix-multiply rate. `measure.py --info-only` now also measures the launch cost and the matrix-multiply rate. v2 fits the reference data (3 parameters, 9 points) with 8 of 9 within 20% in-sample; **that is not a test**, since the points were used for the fit. The test is the friends' GPUs. Bars unchanged. Predictions from v2 are committed before each friend runs a model; v1 predictions are not made. If v2 fails on most friends' GPUs, the planner idea is withdrawn as stated, and the finding that small-model decode on this stack is software-bound stays as the result.

## Amendment 2 (31 Oct 2026, before any friend's run): what each machine tests

Most friends have the same GPU model as the reference (an RTX 3050); one has an RTX 4060. So: (a) a machine with the **same GPU model** is a **noise and CPU-scaling check** (how far two laptops with the same GPU differ, and whether the launch-cost scaling of v2 works); it does not count toward the cross-GPU claim; (b) the **cross-GPU bar** (G1-speed and G1-energy, unchanged) is evaluated on the machines with a different GPU model: the 4060 and any free cloud GPU (for example a Colab or Kaggle card) added later. The measured spread between same-GPU machines is reported next to the bars: if it exceeds 20%, the bars are unrealistic for any predictor and that is the finding. With one or two different-GPU machines the conclusion can only be 'consistent with' or 'not consistent with' the predictor working, not a general claim.

## What this does not show

Four consumer GPUs in laptops or desktops say little about data-centre cards; board power from `nvidia-smi` is not wall power and its accuracy is not known; software versions and power modes change results (record them, same mains and mode for each run); half precision only; one decode implementation (the library's default); no quality measure.

Result so far: [RESULT](RESULT.md).

Files: [`measure.py`](measure.py), [`predict.py`](predict.py), [`report.py`](report.py); friends' guide: [README](README.md); tested end to end on a CPU with a tiny model only (no GPU available to the builder).

Related: [Research 01 summary](../../../docs/reviews/research_01_summary.md), [Jarvis response to research 01](../../../docs/reviews/jarvis_response_research_01.md), [Measurement protocol](../../../docs/measurement_protocol.md), [Hardware index](../../HARDWARE_INDEX.md)
