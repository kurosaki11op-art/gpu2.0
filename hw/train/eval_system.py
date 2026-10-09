"""Evaluate a trained SPARK model as a full system, with the bit-exact golden model.

1. Exact-match check: PyTorch integer-mode predictions vs golden predictions.
2. Calibrate the early-exit threshold on a calibration split.
3. Accuracy and work for: main path only, early exit, recall, adaptive controller.

Usage: python3 hw/train/eval_system.py --run hw/train/out_qat_sp0.05 [--bytes 2000]
"""
import argparse
import json
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as sg  # noqa: E402
import train_spark_v0 as tr  # noqa: E402


def load_torch(npz, cfg):
    z = np.load(npz)
    ctx = 1 + sum(1 for k in z.files if k.startswith("emb") and k != "emb")
    m = tr.SparkV0(a=cfg["a"], acc_sh=cfg["acc_sh"], s_sh=cfg["s_sh"], ctx=ctx,
                   spike_mode="thr" if "th0" in z.files else "sym").double()
    with torch.no_grad():
        m.emb.copy_(torch.from_numpy(z["emb"].astype(np.float64)))
        for i, e in enumerate(m.embx):
            e.copy_(torch.from_numpy(z[f"emb{i + 1}"].astype(np.float64)))
        for name, key in [("w0", "w0"), ("w1", "w1"), ("we", "w_exit"), ("wm", "w_main")]:
            getattr(m, name).copy_(torch.from_numpy(z[key].astype(np.float64)))
        if "th0" in z.files:
            m.th0.copy_(torch.from_numpy(z["th0"].astype(np.float64)))
            m.th1.copy_(torch.from_numpy(z["th1"].astype(np.float64)))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="training output folder")
    ap.add_argument("--bytes", type=int, default=2000)
    a = ap.parse_args()
    cfg = {"a": 230, "acc_sh": 2, "s_sh": 4}
    rj = os.path.join(a.run, "spark_v0_config.json")
    if os.path.exists(rj):
        cfg.update({k: v for k, v in json.load(open(rj)).items() if k in cfg})
    npz = os.path.join(a.run, "spark_v0_model.npz")
    tr.RELAX[0] = False

    data = tr.load_corpus(3_000_000)
    n = len(data)
    cal = data[int(n * 0.9): int(n * 0.9) + a.bytes]
    test = data[int(n * 0.95): int(n * 0.95) + a.bytes]

    m = load_torch(npz, cfg)
    with torch.no_grad():
        lm, le, _, _, _ = m(torch.from_numpy(test.astype(np.int64))[None, :])
        torch_pred = lm[0].argmax(-1).numpy()
        lmc, lec, _, _, _ = m(torch.from_numpy(cal.astype(np.int64))[None, :])
    W = sg.Weights.from_npz(npz)
    mode = "thr" if W.th is not None else "sym"

    # exit threshold calibration (calibration split, never the test split)
    le_c, lm_c = lec[0].numpy(), lmc[0].numpy()
    srt = np.sort(le_c, axis=1)
    margin = srt[:, -1] - srt[:, -2]
    ex_pred, main_pred, truth = le_c.argmax(1)[:-1], lm_c.argmax(1)[:-1], cal[1:]
    exit_th = int(margin.max()) + 1
    for th in sorted(set(int(x) for x in np.percentile(margin, np.arange(5, 100, 5)))):
        sel = margin[:-1] >= th
        if sel.sum() >= 20 and np.mean(ex_pred[sel] == truth[sel]) >= np.mean(main_pred[sel] == truth[sel]):
            exit_th = th
            break

    base = dict(a=cfg["a"], acc_sh=cfg["acc_sh"], s_sh=cfg["s_sh"], spike_mode=mode)
    systems = {
        "main path only": dict(),
        "early exit": dict(exit_en=1, exit_th=exit_th),
        "recall": dict(recall=1, conf_th=1),
        "adaptive (recall + change-only/full + adaptive exit)": dict(adapt=1, recall=1, conf_th=1,
                                                                     exit_en=1, exit_th=exit_th),
    }
    out = {"run": a.run, "eval_bytes": int(len(test)), "exit_th": exit_th}
    for name, ov in systems.items():
        g = sg.Golden(W, sg.Cfg(**base, **ov))
        preds, paths, events = [], [], []
        for b in test:
            o = g.step(int(b))
            preds.append(o["pred"])
            paths.append(o["path"])
            events.append(sum(o["proc"]))
        preds = np.array(preds)
        res = {"accuracy": float(np.mean(preds[:-1] == test[1:])),
               "events_per_token": float(np.mean(events)),
               "paths_full_exit_recall": [int(np.sum(np.array(paths) == p)) for p in range(3)]}
        if name == "main path only":
            res["torch_vs_golden_mismatches"] = int(np.sum(preds != torch_pred))
        out[name] = res
        print(f"{name:55s} acc {res['accuracy']:.1%}  events/token {res['events_per_token']:.1f}  "
              f"paths {res['paths_full_exit_recall']}"
              + (f"  torch-vs-golden mismatches {res['torch_vs_golden_mismatches']}" if "torch_vs_golden_mismatches" in res else ""),
              flush=True)
    # dense reference work: every input processed in every stage
    out["dense_events_per_token"] = float(64 * W.w[0].shape[1] // 64 + 128 + 128)
    json.dump(out, open(os.path.join(a.run, "system_eval.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
