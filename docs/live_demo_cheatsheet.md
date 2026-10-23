---
title: Live demo cheat sheet (chip vs CNN on the laptop GPU)
date: 2026-10-23
tags: [pitch, demo, benchmark]
---

# Live demo: L Cortex against a CNN on your GPU

## Before the judge watches (2 minutes)

Open PowerShell and run:
```
cd D:\L
git pull
python -c "import torch; print('GPU found:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"
iverilog -V
dir D:\cortex_data\mnist.npz
```
Expected: `GPU found: True NVIDIA GeForce RTX 3050 6GB Laptop GPU`, an Icarus Verilog version line, and the mnist.npz file listed. If torch says False, install the CUDA build: `pip install torch --index-url https://download.pytorch.org/whl/cu121`. If iverilog is not found, add its folder to PATH (for example `C:\iverilog\bin`) and open a new PowerShell.

## Test A: speed and energy per decision (about 1 to 2 minutes)

```
cd D:\L
python virtual_space\benchmark.py D:\cortex_data
```
It prints one table. Last time on your laptop: chip FPGA build 55.7 us (17,952 decisions/s), chip pipelined 11.7 us (85,174 decisions/s), GPU batch 1 about 1,800 us and about 69 mJ, GPU batch 1024 about 22,000 decisions/s and about 1.95 mJ. The chip rows are cycles from the RTL simulation at 27 MHz (time and energy ESTIMATED); the GPU rows are MEASURED.

## Test B: accuracy and forgetting, chip against the CNN (a few minutes)

```
cd D:\L
python hw\brain\experiments\month4\chip_vs_gpu.py D:\cortex_data
```
Faster rehearsal: add `--seeds 1`. Clothing instead of digits: add `--ds fashion` (needs the Fashion files in the data folder). Last time (digits, 59,063 images): chip all at once 97.91%, in stages 95.51%; CNN all at once 99.09% (1,148 J), in stages 19.60% (510 J).

## What to say while it runs

- Test A: "The chip rows are the real design running in a simulator, cycles counted exactly, time at 27 MHz. The GPU rows are measured on this laptop. The chip energy is an estimate until the board run."
- Test B: "Both learn the same images. All at once the CNN is about a point ahead. Learn two classes at a time and the CNN forgets (about 20%); the chip keeps about 95%."

## If something fails live

Say "the chip side is the integer model, bit-exact with the RTL" and show the saved results in the journal or on slide 14. Do not retry more than once in front of the judge.

## The idea in one breath

The picture becomes on/off bits with simple comparisons. Only the bits that are on are written into a short list. The chip reads only those rows of the table and adds the scores; the biggest total wins. A GPU does the arithmetic for every number, zeros included.

Related: [Final pitch script](pitch_script_final.md), [Pitch Q&A sheet](pitch_qa_sheet.md), [Index](INDEX.md)
