#!/usr/bin/env python3
"""Pre-registered predictor for test G1. Two steps.
  fit:      python predict.py fit REF_RESULTS.json [REF_RESULTS2.json ...] --out fit.json      (reference GPU only: the founder's)
  predict:  python predict.py predict fit.json INFO.json MODEL_STATS.json --out predictions.json (a different GPU; INFO from measure.py --info-only; MODEL_STATS = a reference results file for the same model, only its model fields are used)
Model (decode is memory bound): t_step = a * step_bytes + t0, with step_bytes = weight_bytes + B * ctx * 2 * layers * kv_heads * head_dim * 2 (fp16 K and V), ctx = prompt + new/2.
On the target GPU, a is scaled by the ratio of copy bandwidths (a_target = a_ref * bw_ref / bw_target); t0 is kept.
Power: P_net = c * u with u = (step_bytes / t_step) / (copy bandwidth); c fitted on the reference GPU. Prediction: P = idle_target + c * u. J per token = P * t_step / B.
The rule is fixed before any other GPU is measured; do not change it after seeing results."""
import json, sys
import numpy as np

def stats(r, run):
    hd = r["hidden"] // r["heads"]; ctx = r["prompt"] + r["new"] / 2
    return r["weight_bytes"] + run["batch"] * ctx * 2 * r["layers"] * r["kv_heads"] * hd * 2

def fit(files, out):
    xs, ys, us, ps = [], [], [], []; ref = None
    for f in files:
        r = json.load(open(f)); ref = ref or r
        for run in r["runs"]:
            if "error" in run: continue
            sb = stats(r, run); tstep = run["seconds"] / run["new_tokens"]; xs.append(sb); ys.append(tstep)
            if run.get("mean_power_w") is not None and r.get("idle_power_w") is not None:
                us.append(sb / tstep / (r["bandwidth_copy_gbs"] * 1e9)); ps.append(run["mean_power_w"] - r["idle_power_w"])
    A = np.vstack([xs, np.ones(len(xs))]).T; (a, t0), *_ = np.linalg.lstsq(A, np.array(ys), rcond=None)
    c = float(np.sum(np.array(us) * np.array(ps)) / np.sum(np.array(us) ** 2)) if us else None
    json.dump({"a": a, "t0": t0, "c": c, "bw_ref_gbs": ref["bandwidth_copy_gbs"], "gpu_ref": ref["gpu"], "points": len(xs)}, open(out, "w"), indent=1); print("fit", a, t0, c)

def predict(fitf, infof, statsf, out):
    f = json.load(open(fitf)); info = json.load(open(infof)); m = json.load(open(statsf)); preds = []
    a = f["a"] * f["bw_ref_gbs"] / info["bandwidth_copy_gbs"]
    for B in (1, 4, 16):
        run = {"batch": B}; sb = stats(m, run); tstep = a * sb + f["t0"]; fits = sb <= 0.9 * info["vram_gb"] * 1e9
        p = {"batch": B, "fits_in_memory": bool(fits), "tokens_per_s_per_user": 1 / tstep, "tokens_per_s_total": B / tstep}
        if f["c"] is not None and info.get("idle_power_w") is not None:
            u = sb / tstep / (info["bandwidth_copy_gbs"] * 1e9); P = info["idle_power_w"] + f["c"] * u; p["power_w"] = P; p["joules_per_token_gross"] = P * tstep / B
        preds.append(p)
    json.dump({"gpu": info["gpu"], "model": m["model"], "predictions": preds}, open(out, "w"), indent=1); print(json.dumps(preds, indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]; o = a[a.index("--out") + 1] if "--out" in a else "out.json"
    if a[0] == "fit": fit([x for x in a[1:] if x != "--out" and x != o], o)
    else: predict(a[1], a[2], a[3], o)
