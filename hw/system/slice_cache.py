"""Cached per-byte outputs for the calibration and test slices:
SPARK v2 (pred, conf, path, bucket) and GPU-side models (greedy pred, max softmax prob, prob of SPARK's guess)."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa
OUT = os.path.join(HERE, "out", "slice_cache.npz")


def slices(nbytes=20000):
    data = tr.load_corpus(3_000_000); n = len(data)
    return {"cal": data[int(n * 0.9): int(n * 0.9) + nbytes], "test": data[int(n * 0.95): int(n * 0.95) + nbytes]}


def spark(d):
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0,
                              exit_en=1, exit_th=16), tb=12, lut=lut)
    r = [g.step(int(b)) for b in d]
    return (np.array([o["pred"] for o in r]), np.array([o["conf"] for o in r]) / 255.0,
            np.array([o["path"] for o in r]), np.array([o["bucket"] for o in r]))


def gpu(path, d, spred):
    ck = torch.load(path); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
    x = torch.from_numpy(d.astype(np.int64)); n = len(d)
    pred = np.zeros(n, int); pmax = np.zeros(n); psp = np.zeros(n)
    with torch.no_grad():
        for s in range(0, n, 64):
            lo = max(0, s - 64); hi = min(n, s + 64)
            lg, _ = m(x[lo:hi][None], targets=x[lo:hi][None])
            pr = torch.softmax(lg[0, s - lo:hi - lo].float(), -1).numpy()
            pred[s:hi] = pr.argmax(1); pmax[s:hi] = pr.max(1); psp[s:hi] = pr[np.arange(hi - s), spred[s:hi]]
    return pred, pmax, psp


if __name__ == "__main__":
    S = slices(); out = {}
    for k, d in S.items():
        out[f"{k}_text"] = d
        sp, cf, pa, bk = spark(d); out[f"{k}_sp"], out[f"{k}_conf"], out[f"{k}_path"], out[f"{k}_bucket"] = sp, cf, pa, bk
        for name, path in (("big", "out_big/gpu_model.pt"), ("small", "out/gpu_model.pt")):
            p, pm, ps = gpu(os.path.join(HERE, path), d, sp)
            out[f"{k}_{name}_pred"], out[f"{k}_{name}_pmax"], out[f"{k}_{name}_psp"] = p, pm, ps
        print(k, "done", flush=True)
    np.savez(OUT, **out)
