# SPARK core v0 — working RTL

An event-driven, "think-less" inference core for a small L-style spiking model, written in Verilog, verified bit-exact against a Python reference model, and synthesised for the Tang Nano 20K FPGA (Gowin GW2AR-18).

## What it implements
| Mechanism | Hardware | Config switch |
|---|---|---|
| Skip silent neurons (event-driven) | Scanner builds a mask of non-zero inputs; the MAC engine only runs for those | `sparse_en` (0 = dense, GPU-style) |
| Change-only spikes (delta) | Remembers last value sent per input; persistent accumulators; only changes become events | `delta_en` |
| Early exit (confidence gate) | Exit head on layer-0 spikes; argmax + top-1/top-2 margin; skips layer 1 and the main head | `exit_en`, `exit_th` |
| Recall instead of recompute (hippocampus) | 1,024-entry hash table on the last 4 bytes with a 2-bit confidence counter; confident hit skips every layer | `recall_en`, `conf_th` |
| Energy cap | Maximum non-zero events per stage per token | `cap` |
| 4-bit datapath | int4 weights and spikes, 16 lanes, integer-only (no floating point) | — |
| Memory beside compute | All weights, accumulators, membranes and spikes in on-chip block RAM | — |
| Work counters | Cycles per token, weight words read, busy cycles per unit (engine, scan, post, recall) | — |

Model size (demo): byte → 64-wide embedding → 128 spiking neurons → 128 spiking neurons → 256 logits, plus a 256-logit exit head. Weights are random sparse int4 **demo weights**; trained L-Edge weights replace them via the export in `prompts/L_architecture_changes_prompt.txt` (Phase 3).

## Files
- `golden/spark_golden.py` — bit-exact integer reference model, weight generator, hex export.
- `rtl/spark_ram.v` — synchronous RAM/ROM (infers block RAM).
- `rtl/spark_core.v` — the core (FSM + datapath).
- `tb/tb_spark_core.v` — testbench; one result line per token.
- `run_sim.py` — builds, simulates every configuration, compares each token with the golden model, writes `results/sim_results.md`.
- `synth/synth_gowin.ys` — Yosys synthesis for the Gowin GW2AR-18; utilisation in `synth/utilization.txt`.

## Run
```
sudo apt-get install iverilog yosys     # once
python3 hw/run_sim.py                   # simulation + golden check
cd hw/synth && yosys -l synth.log synth_gowin.ys
```

## Known limits of v0 (honest list)
- Demo weights, not trained L weights → prediction quality is meaningless here; the results show **work saved** and **correctness vs the reference model**, not language-model accuracy.
- Energy cap keeps the first k events in input order (not the largest k).
- Lazy membrane updates, fast-weight learning unit, skill memory, prefetch and hot/cold split are not in v0.
- Timing closure, place-and-route and on-board power measurement are the next steps (nextpnr / Gowin EDA, then INA219 on the board).
