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

## What this does not show

Four consumer GPUs in laptops or desktops say little about data-centre cards; board power from `nvidia-smi` is not wall power and its accuracy is not known; software versions and power modes change results (record them, same mains and mode for each run); half precision only; one decode implementation (the library's default); no quality measure.

Files: [`measure.py`](measure.py), [`predict.py`](predict.py).

Related: [Research 01 summary](../../../docs/reviews/research_01_summary.md), [Jarvis response to research 01](../../../docs/reviews/jarvis_response_research_01.md), [Measurement protocol](../../../docs/measurement_protocol.md), [Hardware index](../../HARDWARE_INDEX.md)
