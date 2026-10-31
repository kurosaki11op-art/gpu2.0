---
title: How to run the speed and energy check on your own GPU (friends' guide, 31 Oct 2026)
tags: [spark, gpu, measurement, guide, wedge]
---

# Speed and energy check for your GPU

What you get: how fast a language model really runs on your GPU, how much power it draws, and what the electricity costs per million tokens, with the best batch size for your card. It takes about 15 minutes. It reads nothing from your files and sends nothing anywhere; you choose whether to send me the result file.

## One-time setup

1. Python 3.10 or newer. Then: `pip install torch transformers` (use the CUDA build of torch from pytorch.org for your NVIDIA card).
2. Plug a laptop into mains power. Set the same power mode every time. Close games, browsers and other heavy programs.
3. Check `nvidia-smi` works in a terminal. If it shows a power number in watts, energy is measured; if it shows N/A, only speed is.

## Run

1. Quick GPU info (30 seconds, runs no model): `python measure.py x --info-only --out info.json`. Send me `info.json` first; I will send back predictions so nothing is tuned afterwards.
2. For each model I give you: `python measure.py MODEL_NAME --out result_MODEL.json` (a few minutes each; the first run downloads the model).
3. Report: `python report.py result_*.json --kwh-price 8 --currency INR` (use your own price per kWh). It prints and saves `report.md`.
4. Send me the `result_*.json` files. They contain your GPU name, memory speed, power readings and timings; no personal data.

If a batch size runs out of memory the tool says so and goes on; that is a useful result too.

Protocol and bars (written before any friend runs anything): [PROTOCOL.md](PROTOCOL.md). Scripts: [measure.py](measure.py), [report.py](report.py), [predict.py](predict.py).

Related: [Protocol](PROTOCOL.md), [Hardware index](../../HARDWARE_INDEX.md)
