#!/usr/bin/env python3
"""M1 fix, second metric (31 Oct 2026): next-character cross-entropy of the transformer in fp32, INT8 weights, W8A8 and the mixed-precision configuration, on the original and the fresh evaluation windows.
usage: python m1_loss_check.py WORKDIR   (after export_models.py and m1_fix.py)"""
import json, os, subprocess, sys
import numpy as np
W = sys.argv[1]; V, T = 128, 64
def nll(d, mode):
    ids = np.fromfile(f"{d}/inputs.bin", np.float32).reshape(-1, T).astype(np.int64); lg = np.fromfile(f"{d}/out_{mode}.bin", np.float32).reshape(-1, T, V); lg = lg - lg.max(-1, keepdims=True)
    lp = lg - np.log(np.exp(lg).sum(-1, keepdims=True)); return float(-np.take_along_axis(lp[:, :-1], ids[:, 1:][..., None], -1).mean())
chosen = json.load(open(os.path.join(W, "m1_fix.json")))["chosen_int16"]; out = {}
for name, d in (("original_eval", os.path.join(W, "lm")), ("fresh_eval", os.path.join(W, "lm_eval2"))):
    base = open(os.path.join(d, "program.txt")).read(); final = "\n".join((l + " a16") if l.startswith("W ") and l.split()[1] in chosen else l for l in base.splitlines()) + "\n"; r = {}
    for mode in ("fp32", "w8", "int8"): subprocess.run(["/tmp/gpu_sim", d, mode, "16"], check=True, capture_output=True); r[mode] = nll(d, mode)
    open(os.path.join(d, "program.txt"), "w").write(final); subprocess.run(["/tmp/gpu_sim", d, "int8", "16"], check=True, capture_output=True); r["mixed"] = nll(d, "int8"); open(os.path.join(d, "program.txt"), "w").write(base)
    out[name] = dict(nll=r, loss_increase_over_fp32={k: v - r["fp32"] for k, v in r.items() if k != "fp32"})
print(json.dumps(out, indent=1)); json.dump(out, open(os.path.join(W, "m1_loss_check.json"), "w"), indent=1)
