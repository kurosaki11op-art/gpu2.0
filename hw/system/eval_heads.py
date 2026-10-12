"""Output-head format study: agreement with the GPU stand-in model, with early exit on and off, plus work per byte.
usage: python eval_heads.py <dir> [<dir> ...]    (all models are 64/32). Exit and arbitration thresholds are matched by exit RATE:
each model's thresholds are set so it takes the early exit on the same fraction of bytes as the first (reference) model."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
g1.H, g1.D = 64, 32
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
N = int(os.environ.get("NB", 6000)); cal_t = Z["cal_text"][:3000]; text, big = Z["test_text"][:N], Z["test_big_pred"][:N]
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]


def run(W, data, exit_en, exit_th):
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=2, exit_en=exit_en, exit_th=exit_th)
    cfg.arb_th = 64
    g = g2.GoldenV2(W, cfg, tb=12, lut=lut)
    return [g.step(int(b)) for b in data]


def margins(W):
    r = run(W, cal_t, 1, 10 ** 9)                       # threshold never met: records every exit margin
    m = np.array([o["mexit"] for o in r if o["mexit"] >= 0]); return m


ref_rate = None; rows = {}
for name in sys.argv[1:]:
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", name, "spark_v0_model.npz"))
    m = margins(W)
    if ref_rate is None:
        ref_th = 16; ref_rate = float((m >= ref_th).mean()); th = ref_th
    else:
        th = int(np.quantile(m, 1 - ref_rate))
    out = {"exit_th": th, "exit_rate_cal": float((m >= th).mean())}
    for label, ee in (("exit_on", 1), ("exit_off", 0)):
        r = run(W, text, ee, th); pred = np.array([o["pred"] for o in r])
        ag = pred[:-1] == big[:-1]; runs = np.diff(np.flatnonzero(np.concatenate([[1], ~ag, [1]]))) - 1
        out[label] = {"agree": float(ag.mean()), "mean_run": float(runs.mean()),
                      "events_per_byte": float(np.mean([sum(o["ev"]) for o in r]))}
    rows[name] = out; print(name, json.dumps(out), flush=True)
json.dump(rows, open(os.path.join(HERE, "..", "results", "head_format_eval.json"), "w"), indent=1)
