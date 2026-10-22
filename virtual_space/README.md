---
title: Virtual space: chip vs GPU benchmark
date: 2026-10-22
tags: [L, benchmark, docker]
---
# Virtual space: chip vs GPU benchmark

One container, your GPU, the chip as its RTL design in a simulator, one table. Commands for Windows (Docker Desktop with WSL2 and the NVIDIA container toolkit) and for a plain Python environment.

**Docker (a clean virtual space):** from the repo folder (for example `D:\\L`):
```
docker build -t l-chip-gpu-bench -f virtual_space/Dockerfile .
docker run --rm --gpus all -v D:\\cortex_data:/data l-chip-gpu-bench
docker run --rm --gpus all -v D:\\cortex_data:/data l-chip-gpu-bench --accuracy
```
`D:\\cortex_data` must contain `mnist.npz`. The second run also does the accuracy comparison (virtual chip vs GPU CNN on the same images).

**Without Docker (a Python virtual environment):** install Icarus Verilog (iverilog and vvp on PATH), then
```
python -m venv D:\\venv_l && D:\\venv_l\\Scripts\\activate
pip install numpy numba nvidia-ml-py
pip install torch --index-url https://download.pytorch.org/whl/cu121
python virtual_space/benchmark.py D:\\cortex_data
```

What it measures: cycles per decision, learn and dream of the chip's RTL at the real size (SIMULATED, exact for the design), times at 27 MHz (MODELLED), the deck's estimated energy per decision (ESTIMATED), and on your GPU the latency, throughput and energy per decision of a small CNN (MEASURED). The chip and the CNN do different work: this compares the cost of one decision.

Related: [Docs index](../docs/INDEX.md), [Project memory](../docs/PROJECT_MEMORY.md)
