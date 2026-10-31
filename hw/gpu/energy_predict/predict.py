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

# ---- v2 (amendment of 31 Oct 2026, written after the reference GPU was measured and before any other GPU): v1 fitted its own reference data badly (1 of 9 points within 20%); per-layer time was almost constant, so decode on this software stack is limited by per-layer launch overhead, not by memory bandwidth.
# v2: t_step = layers * g + a * step_bytes + e * flops, with flops = 2 * parameters * batch. Fitted on the reference GPU (3 parameters, 9 points). For another machine: g is scaled by (launch us per op of the target / reference), a by (reference copy bandwidth / target), e by (reference matmul TFLOPs / target).
# Power (v2): P_net = p0 + p1 * u, u = (step_bytes / t_step) / copy bandwidth, fitted on the reference GPU; P = target idle power + P_net; joules per token = P * t_step / batch.
def feats(r, run):
    sb = stats(r, run); fl = 2 * (r["weight_bytes"] / r["dtype_bytes"]) * run["batch"]; return [r["layers"], sb, fl], sb

def fit2(files, ref_info, out):
    rows, ys, us, ps = [], [], [], []; ref = None
    for f in files:
        r = json.load(open(f)); ref = ref or r
        for run in r["runs"]:
            if "error" in run: continue
            x, sb = feats(r, run); rows.append(x); ys.append(run["seconds"] / run["new_tokens"])
            if run.get("mean_power_w") is not None and r.get("idle_power_w") is not None:
                us.append((sb / ys[-1]) / (r["bandwidth_copy_gbs"] * 1e9)); ps.append(run["mean_power_w"] - r["idle_power_w"])
    c, *_ = np.linalg.lstsq(np.array(rows), np.array(ys), rcond=None)
    pf = np.polyfit(us, ps, 1) if len(us) >= 2 else [None, None]; info = json.load(open(ref_info))
    d = {"g": c[0], "a": c[1], "e": c[2], "p1": float(pf[0]), "p0": float(pf[1]), "bw_ref_gbs": ref["bandwidth_copy_gbs"], "launch_ref_us": info["launch_us_per_op"], "tflops_ref": info["matmul_tflops"], "gpu_ref": ref["gpu"], "points": len(rows)}
    json.dump(d, open(out, "w"), indent=1); print("fit v2", d)

def predict2(fitf, infof, statsf, out):
    f = json.load(open(fitf)); info = json.load(open(infof)); m = json.load(open(statsf)); preds = []
    g = f["g"] * info["launch_us_per_op"] / f["launch_ref_us"]; a = f["a"] * f["bw_ref_gbs"] / info["bandwidth_copy_gbs"]; e = f["e"] * f["tflops_ref"] / info["matmul_tflops"]
    for B in (1, 4, 16):
        run = {"batch": B}; x, sb = feats(m, run); t = g * x[0] + a * x[1] + e * x[2]; fits = sb <= 0.9 * info["vram_gb"] * 1e9
        p = {"batch": B, "fits_in_memory": bool(fits), "tokens_per_s_per_user": 1 / t, "tokens_per_s_total": B / t}
        if info.get("idle_power_w") is not None and f["p1"] is not None:
            u = (sb / t) / (info["bandwidth_copy_gbs"] * 1e9); P = info["idle_power_w"] + f["p0"] + f["p1"] * u; p["power_w"] = P; p["joules_per_token_gross"] = P * t / B
        preds.append(p)
    json.dump({"version": "v2", "gpu": info["gpu"], "model": m["model"], "predictions": preds}, open(out, "w"), indent=1); print(json.dumps(preds, indent=1))

if __name__ == "__main__":
    a = sys.argv[1:]; o = a[a.index("--out") + 1] if "--out" in a else "out.json"
    if a[0] == "fit": fit([x for x in a[1:] if x != "--out" and x != o], o)
    elif a[0] == "fit2": ri = a[a.index("--ref-info") + 1]; fit2([x for x in a[1:] if x not in ("--out", o, "--ref-info", ri)], ri, o)
    elif a[0] == "predict2": predict2(a[1], a[2], a[3], o)
    else: predict(a[1], a[2], a[3], o)
