#!/usr/bin/env python3
"""M1 fix (31 Oct 2026): per-layer activation precision (INT8 default, INT16 where needed) chosen on a calibration set, evaluated on the original evaluation set and a fresh one.
Plan and bars: hw/gpu/M1_fix_plan.md (written before the change). usage: python m1_fix.py WORKDIR   (WORKDIR from export_models.py, with /tmp/gpu_sim built)"""
import json, os, shutil, subprocess, sys
import numpy as np
W = sys.argv[1]; SIM = "/tmp/gpu_sim"; T = 64; V = 128
def windows(offset, n=16):
    from datasets import load_dataset
    txt = "\n".join(load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")["text"]); ids = np.frombuffer(txt.encode("ascii", "ignore"), np.uint8).astype(np.int64) % V
    return np.stack([ids[offset + i * 4001: offset + i * 4001 + T] for i in range(n)]).astype(np.float32)
def make_dir(name, ids):
    d = os.path.join(W, name); os.makedirs(d, exist_ok=True)
    for f in ("tensors.bin", "manifest.txt", "input.txt"): shutil.copy(os.path.join(W, "lm", f), os.path.join(d, f))
    ids.tofile(os.path.join(d, "inputs.bin")); return d
def run(d, mode, n=16, program=None):
    if program is not None: open(os.path.join(d, "program.txt"), "w").write(program)
    subprocess.run([SIM, d, mode, str(n)], check=True, capture_output=True); return np.fromfile(os.path.join(d, "out_%s.bin" % mode), np.float32).reshape(-1, V)
base = open(os.path.join(W, "lm", "program.txt")).read().splitlines(); wnames = [l.split()[1] for l in base if l.startswith("W ") and l.split()[1] not in ("tok", "pos")]
def prog(prec):  # prec: dict name -> 'a16' | 'af'
    return "\n".join((l + " " + prec[l.split()[1]]) if l.startswith("W ") and l.split()[1] in prec else l for l in base) + "\n"
cal, ev1, ev2 = make_dir("lm_cal", windows(100000)), os.path.join(W, "lm"), make_dir("lm_eval2", windows(200000)); res = {}
for d in (cal, ev2): shutil.copy(os.path.join(ev1, "program.txt"), os.path.join(d, "program.txt"))
ref = {d: run(d, "fp32") for d in (cal, ev2)}; ref[ev1] = np.fromfile(os.path.join(ev1, "out_fp32.bin"), np.float32).reshape(-1, V)
agree = lambda d, o: float((o.argmax(1) == ref[d].argmax(1)).mean())
b0 = agree(cal, run(cal, "int8", program=prog({}))); print("calibration: W8A8 baseline agreement %.4f" % b0, flush=True); sens = {}
for n in wnames: sens[n] = agree(cal, run(cal, "int8", program=prog({n: "af"}))) - b0
order = sorted(wnames, key=lambda n: -sens[n]); print("sensitivity (gain in calibration agreement when only this tensor has FP activations):", {n: round(sens[n], 4) for n in order}, flush=True)
chosen, cur = [], b0
while cur < 0.995 and len(chosen) < 5:
    chosen.append(order[len(chosen)]); cur = agree(cal, run(cal, "int8", program=prog({n: "a16" for n in chosen}))); print("  INT16 activations for %s -> calibration agreement %.4f" % (chosen, cur), flush=True)
final = prog({n: "a16" for n in chosen}); out = {}
for nm, d in (("original_eval_1024", ev1), ("fresh_eval_1024", ev2)):
    open(os.path.join(d, "program_a16.txt"), "w").write(final); backup = open(os.path.join(d, "program.txt")).read()
    o0 = run(d, "int8", program=prog({})); o1 = run(d, "int8", program=final); out[nm] = dict(agreement_w8a8=agree(d, o0), agreement_mixed=agree(d, o1), rel_err_mixed=float(np.abs(o1 - ref[d]).max() / np.abs(ref[d]).max()))
    cj = json.load(open(os.path.join(d, "counters_int8.json"))); out[nm]["macs_total"] = cj["total"]["macs"]; out[nm]["macs_int16_activations"] = cj["total"]["macs_int16_activations"]
    open(os.path.join(d, "program.txt"), "w").write(backup)
share = out["original_eval_1024"]["macs_int16_activations"] / out["original_eval_1024"]["macs_total"]
res = dict(calibration_baseline=b0, sensitivity=sens, chosen_int16=chosen, calibration_final=cur, evaluation=out, int16_share_of_macs=share, mac_energy_overhead_if_int16_costs_2x=1 + share)
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(W, "m1_fix.json"), "w"), indent=1)
