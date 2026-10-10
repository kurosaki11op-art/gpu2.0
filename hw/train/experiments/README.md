# Accuracy / brain-like learning experiments

1. `python3 fastsim.py ../out_qat_sp0.05 20000 feats_sp005.npz` — fast exact main-path simulator
   (0 mismatches vs the golden model); dumps spikes and logits for 20,000-byte cal/test streams.
2. `learn.py`, `learn2.py` — on-chip plasticity on the output head (in-place int4, intrinsic bias, fast synapses).
3. `arbiter.py` — learned memory-vs-network arbiter (saturating counters per confidence bucket).
4. `prime.py` (tuned on cal) / `prime_test.py` (cal + test) — multi-scale memory priming.

Results: `hw/results/model_accuracy.md`.
