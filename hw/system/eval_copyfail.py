"""SPARK v2 weights vs the GPU stand-in model, split by whether copy-drafting works at that byte.
usage: python eval_copyfail.py <model_dir> [<model_dir> ...]   (dirs under hw/train, e.g. out_qat_sp0.05)
Metrics on the held-out test slice: agreement with the GPU model's greedy byte, overall and on copy-failure bytes
(no earlier match of the last 8/6/4 bytes, or the match predicts the wrong byte), plus mean agreeing run length."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
text, big = Z["test_text"], Z["test_big_pred"]
N = int(os.environ.get("NB", 12000)); text, big = text[:N], big[:N]
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
fail = tr.copy_fail_mask(text).astype(bool)
rows = {}
for arg in sys.argv[1:]:
    name, _, hd = arg.partition("@")                   # optional "dir@H,D" for a resized model (size study)
    g1.H, g1.D = (int(x) for x in hd.split(",")) if hd else (128, 64)
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", name, "spark_v0_model.npz"))
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=2, exit_en=int(os.environ.get("EXIT_EN", 1)), exit_th=16)   # EXIT_EN=0 isolates the main head
    cfg.arb_th = 64
    g = g2.GoldenV2(W, cfg, tb=12, lut=lut)
    pred = np.array([g.step(int(b))["pred"] for b in text])
    ag = pred[:-1] == big[:-1]; f = fail[:-1]
    runs = np.diff(np.flatnonzero(np.concatenate([[1], ~ag, [1]]))) - 1
    rows[name] = dict(agree_all=float(ag.mean()), agree_copyfail=float(ag[f].mean()), agree_copyok=float(ag[~f].mean()),
                      mean_run=float(runs.mean()), copyfail_frac=float(f.mean()))
    print(name, json.dumps({k: round(v, 4) for k, v in rows[name].items()}), flush=True)
json.dump(rows, open(os.path.join(HERE, "..", "results", "copyfail_eval_%s.json" % "_".join(sys.argv[1:])[:60].replace("@", "-").replace(",", "x")), "w"), indent=1)
