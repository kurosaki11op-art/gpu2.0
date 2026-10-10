# SPARK beside a GPU: system-level simulation

**What was tested.** SPARK sits next to the GPU and sees every token first. If SPARK is confident, it answers
and the GPU stays idle; otherwise the GPU model answers. The route decision is SPARK's `path` output (0 = full
network, 1 = early exit, 2 = recall memory), which the verified chip already reports on every token over UART —
no new hardware was added for routing. Confidence thresholds (`exit_th`, `conf_th`) are the chip's existing UART
config fields.

| Part | What was used | Label |
|---|---|---|
| SPARK | bit-exact golden model of the verified chip (0 mismatches vs RTL and gate-level), `out_qat_sp0.05` weights | SIMULATED |
| GPU model | **nanoGPT** (open-source GPT-2-style transformer, MIT, `third_party/nanogpt/model.py` unmodified), byte level, 4 layers × 256 wide, 3.21 M params, trained here 15 min on CPU on the same corpus split | MEASURED accuracy |
| Data | held-out Python source: operating points picked on a calibration slice (20,000 bytes), reported on a separate test slice (20,000 bytes) | |
| Energy | first-principles GPU decode model (below) + SPARK switching-activity simulation | ESTIMATED / PROJECTED |

Pretrained Hugging Face checkpoints are blocked by this sandbox's network policy. The script is ready to rerun
with a real pretrained code model (e.g. `bigcode/tiny_starcoder_py`, 164 M) once `huggingface.co` is allowed.

## Results on the test slice (20,000 bytes)

GPU-only accuracy: **56.4 %** (calibration slice 68.2 %).

| SPARK setting (chosen on calibration) | Tokens sent to GPU | System accuracy | Accuracy of the tokens SPARK kept |
|---|---|---|---|
| recall conf ≥ 0 + exit margin ≥ 16 (max offload) | **10.2 %** | 68.2 % | 71.6 % |
| recall conf ≥ 1 + exit margin ≥ 32 (SPARK-kept ≥ 80 %) | 30.4 % | 67.4 % | 80.8 % |
| recall conf ≥ 1 + exit margin ≥ 64 (SPARK-kept ≥ 88 %) | 40.9 % | 68.4 % | 88.3 % |
| recall conf ≥ 1 only | 50.3 % | 68.8 % | 89.9 % |

**Honest reading.** The GPU model that fits in this sandbox (3.2 M params, 15 CPU-minutes) is *weaker* than
SPARK on this text, so the system accuracy is higher than GPU-only here — that will not hold with a strong
pretrained GPU model. The result that carries over is the routing: SPARK finds the tokens it gets right with high
precision. At the conservative setting it keeps 59 % of tokens and is right on 88 % of them; with a strong GPU
model the accuracy cost is (tokens kept) × (GPU accuracy − 88 %) on those tokens, which must be measured with a
real pretrained model before claiming it.

## Energy per token (ESTIMATED, batch-1 decode, PROJECTED to real model sizes)

Every token still has to enter the GPU's KV cache, so the GPU's arithmetic (2 × params FLOPs at 0.5 pJ/FLOP) is
always paid — when SPARK answers, that token is batched into the GPU's next call. What SPARK saves is the weight
read from HBM (params × 2 bytes at 4 pJ/bit), which dominates batch-1 decoding. SPARK itself: 104 nJ/token
(upper end of the simulated low-effort range). GPU static/idle power is ignored, which favours the GPU.

| GPU model (projected) | GPU only | SPARK + GPU, 10 % to GPU | 30 % to GPU | 41 % to GPU |
|---|---|---|---|---|
| 1.1 B code LLM | 71.5 mJ | 8.2 mJ (**8.7× less**) | 22.5 mJ (3.2× less) | 29.9 mJ (2.4× less) |
| 7 B code LLM | 455 mJ | 52.5 mJ (**8.7× less**) | 143 mJ (3.2× less) | 190 mJ (2.4× less) |

SPARK's own energy is < 0.2 % of the system total in every row: the saving comes from not waking the GPU's
memory system, not from SPARK being cheap. With large-batch serving the weight read is shared across the batch and
the saving shrinks; the biggest win is batch-1 / edge / interactive decoding.

Reproduce: `python3 hw/system/train_gpu_model.py --block 128 --batch 32 --minutes 15` then
`python3 hw/system/cascade_sim.py` (writes `hw/system/out/cascade_results.json`).
