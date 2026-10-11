"""Which SPARK v2 settings (same silicon, register/LUT settings only) agree most with the GPU model?
Metric: next-byte agreement with the big model's greedy prediction on the held-out test slice, plus the
draft-relevant number: mean run length of consecutive agreements (longer runs = longer accepted drafts)."""
import json, os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as g1, spark_golden_v2 as g2  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
text, big = Z["test_text"], Z["test_big_pred"]
N = int(os.environ.get("NB", 8000))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
rows = []
for conf_th, mode, tb, arb in itertools.product((0, 1, 2), (0, 2), (12, 14), (16, 64, 160)):
    if mode == 0 and arb != 16:
        continue
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=conf_th, recall_mode=mode, exit_en=1, exit_th=16)
    cfg.arb_th = arb
    g = g2.GoldenV2(W, cfg, tb=tb, lut=lut)
    pred = np.array([g.step(int(b))["pred"] for b in text[:N]])
    ag = pred == big[:N]; tr = pred[:-1] == text[1:N]
    runs = np.diff(np.flatnonzero(np.concatenate([[1], ~ag, [1]]))) - 1
    r = dict(conf_th=conf_th, recall_mode=mode, tb=tb, arb_th=arb, agree_gpu=float(ag.mean()), acc_text=float(tr.mean()),
             mean_run=float(runs.mean()))
    rows.append(r); print(r, flush=True)
json.dump(rows, open(os.path.join(HERE, "..", "results", "spark_cfg_sweep.json"), "w"), indent=1)
