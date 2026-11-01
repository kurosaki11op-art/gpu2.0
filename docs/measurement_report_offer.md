---
title: The GPU cost and speed check - one-page description to show people (1 Nov 2026)
tags: [spark, product, report, offer, customer]
---

# The GPU cost and speed check

**What it is.** A 15-minute measurement of how fast an AI model really runs on your GPU, how much power it uses, and what a million tokens costs you, with the settings that cut the cost. You get a one-page report. It runs on your own machine; nothing is uploaded unless you send the result file.

**Who it is for.** Anyone who runs AI models on a GPU they own or rent and pays for it (small AI companies, labs, freelancers, regional cloud providers).

## What we have measured so far (MEASURED, small models, two GPUs, one run per point)

| finding | numbers |
|---|---|
| **Serving several users at once cuts the energy per token a lot** | 8x to 14x less energy per token at batch 16 than at batch 1 on both an RTX 3050 laptop and a Tesla T4; each user gets about 20% to 45% slower |
| **The software setup can matter as much as the GPU** | On the T4, turning on CUDA graphs in a serving engine made the same model 4.7x (0.5B-class) and 2.5x (1.1B-class) faster at batch 1; the default library path left it at 13% to 37% of the speed the memory allows |
| **Cost per million tokens falls with batching** | At an illustrative 25 INR per GPU hour, a 1.1B-class model on the laptop GPU went from 159 INR to 16 INR per million tokens (illustrative price, not a quote) |

Sample report from real runs: [sample_report_3050.md](../hw/gpu/energy_predict/sample_report_3050.md) (prices in it are illustrative).

## What you do

1. Install Python and two packages; run one command per model (guide: [hw/gpu/energy_predict/README.md](../hw/gpu/energy_predict/README.md)).
2. Run the report command with your own electricity price and GPU-hour price.
3. Read the page. If you want help interpreting it or applying the settings, ask.

## What we are asking for

- Ten minutes of feedback: **Was anything in it new to you? Would you use it on your own setup? Would you pay for it, and what would you consider a fair price?**
- Optional: your result files (they contain the GPU name and timings, no personal data) so we can compare machines.

## What it does not do (limits we state up front)

- It measures; it does not predict. Our attempt to predict speed from hardware specs failed on a second GPU (0 of 9 points within 20%), and we say so.
- Board power from the GPU driver is not wall power; one run per point; small models only; results depend on drivers and library versions.
- The CUDA-graphs gain was measured on a Tesla T4 only; on your machine it is something to try, not a promise.
- It is not a chip and not a new GPU. It is a way to find out whether you are wasting money on the GPUs you already have.

## Message you can send (edit freely)

"Hi, I built a small tool that measures how fast an AI model runs on your GPU, what it costs per million tokens and what setting saves the most. On my laptop it showed a 10x difference in cost per token between settings. Would you run it on your machine (15 minutes) and tell me if it was useful? I'd also like to know what you'd pay for something like it."

Related: [Test G1 result](../hw/gpu/energy_predict/RESULT.md), [Test B result](../hw/gpu/graphs_test/PLAN.md), [Restart 2 study](restart_2_weakness_study.md), [Docs index](INDEX.md)
