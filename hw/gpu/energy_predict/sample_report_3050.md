# What your GPU really does with AI models

Measured on this machine. One run per point; board power from nvidia-smi (not wall power); the library's default decode setup (no CUDA graphs).

## distilgpt2 on NVIDIA GeForce RTX 3050 6GB Laptop GPU

- Model weights 0.16 GB; your GPU's memory speed 123 GB/s; idle power 7.6 W.

| users at once (batch) | speed per user (tokens/s) | total speed (tokens/s) | power (W) | energy per token (J) | electricity per million tokens (INR) | GPU cost per million tokens (INR) |
|---|---|---|---|---|---|---|
| 1 | 149.9 | 149.9 | 10.2 | 0.068 | 0.15 | 46.33 |
| 4 | 215.0 | 860.2 | 21.5 | 0.025 | 0.06 | 8.07 |
| 16 | 158.6 | 2537.3 | 27.2 | 0.011 | 0.02 | 2.74 |

**What this means for you**

- **Serve several users at once.** At batch 16 each token costs 6.3x less energy than at batch 1 (0.011 J against 0.068 J). Each user gets 159 tokens/s instead of 150.
- **Cost per million tokens falls from 46.33 to 2.74 INR** at batch 16 (at 25 INR per GPU hour).
- **How close to the memory limit you run:** at batch 1 this setup reaches 20% of the speed the GPU's memory allows for this model.
- **There may be a large gain from the software setup.** In our own test on a different GPU (a Colab T4), turning on CUDA graphs in a serving engine made batch-1 decode 2.5x to 4.7x faster and reached 72% to 95% of the memory limit. **This is not measured on your machine**; treat it as something to try, not a promise.

## Qwen/Qwen2.5-0.5B on NVIDIA GeForce RTX 3050 6GB Laptop GPU

- Model weights 0.99 GB; your GPU's memory speed 123 GB/s; idle power 8.1 W.

| users at once (batch) | speed per user (tokens/s) | total speed (tokens/s) | power (W) | energy per token (J) | electricity per million tokens (INR) | GPU cost per million tokens (INR) |
|---|---|---|---|---|---|---|
| 1 | 35.1 | 35.1 | 26.5 | 0.756 | 1.68 | 197.81 |
| 4 | 36.0 | 143.8 | 26.7 | 0.186 | 0.41 | 48.28 |
| 16 | 38.1 | 609.4 | 33.7 | 0.055 | 0.12 | 11.40 |

**What this means for you**

- **Serve several users at once.** At batch 16 each token costs 13.7x less energy than at batch 1 (0.055 J against 0.756 J). Each user gets 38 tokens/s instead of 35.
- **Cost per million tokens falls from 197.81 to 11.40 INR** at batch 16 (at 25 INR per GPU hour).
- **How close to the memory limit you run:** at batch 1 this setup reaches 28% of the speed the GPU's memory allows for this model.
- **There may be a large gain from the software setup.** In our own test on a different GPU (a Colab T4), turning on CUDA graphs in a serving engine made batch-1 decode 2.5x to 4.7x faster and reached 72% to 95% of the memory limit. **This is not measured on your machine**; treat it as something to try, not a promise.

## TinyLlama/TinyLlama-1.1B-Chat-v1.0 on NVIDIA GeForce RTX 3050 6GB Laptop GPU

- Model weights 2.20 GB; your GPU's memory speed 123 GB/s; idle power 8.1 W.

| users at once (batch) | speed per user (tokens/s) | total speed (tokens/s) | power (W) | energy per token (J) | electricity per million tokens (INR) | GPU cost per million tokens (INR) |
|---|---|---|---|---|---|---|
| 1 | 43.6 | 43.6 | 34.6 | 0.792 | 1.76 | 159.14 |
| 4 | 38.0 | 152.0 | 37.2 | 0.244 | 0.54 | 45.68 |
| 16 | 26.8 | 429.5 | 41.3 | 0.096 | 0.21 | 16.17 |

**What this means for you**

- **Serve several users at once.** At batch 16 each token costs 8.2x less energy than at batch 1 (0.096 J against 0.792 J). Each user gets 27 tokens/s instead of 44.
- **Cost per million tokens falls from 159.14 to 16.17 INR** at batch 16 (at 25 INR per GPU hour).
- **How close to the memory limit you run:** at batch 1 this setup reaches 78% of the speed the GPU's memory allows for this model.
- Your setup is already close to the memory limit at batch 1; the remaining gain is from batching.

---
Notes: energy is board power from nvidia-smi, not wall power; results depend on drivers, library versions and power mode; one run per point; small models only. Tool and method: hw/gpu/energy_predict in the project repository.
