"""SPARK + GPU system simulation: SPARK sits beside the GPU and routes every token.

For each byte of held-out Python source:
  1. SPARK (bit-exact golden model of the verified chip, out_qat_sp0.05 weights) runs first.
     Its path output (a chip pin / UART reply field: 0 = full network, 1 = early exit,
     2 = recall memory) is the route decision.  path 1 or 2 -> SPARK answers, GPU stays idle.
  2. Otherwise the GPU model answers: nanoGPT byte-level transformer (train_gpu_model.py).
Accuracy is next-byte accuracy against the real text.  Operating points (exit_th, conf_th) are
chosen on a calibration slice and reported on a separate test slice.

GPU energy (ESTIMATED, first principles, batch 1 decode, static power excluded which favours the GPU):
  every token still enters the GPU's KV cache, so its compute is always paid (2 * params FLOPs,
  done as batched catch-up when SPARK skipped it); only tokens the GPU must answer pay the weight
  read from memory (params * 2 bytes, fp16), which dominates at batch 1.
SPARK energy: switching-activity simulation results (hw/power, 56-275 nJ/token depending on effort).
"""
import argparse, json, os, sys
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "third_party", "nanogpt"))
sys.path.insert(0, os.path.join(HERE, "..", "train"))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
from model import GPT, GPTConfig          # noqa: E402
import spark_golden as sg                 # noqa: E402
import train_spark_v0 as tr               # noqa: E402

E_FLOP = 0.5e-12      # J per FP16 FLOP on a modern tensor-core GPU (energy of the arithmetic + on-chip moves)
E_HBM_BIT = 4e-12     # J per bit read from HBM
SPARK_J = {"low": 104e-9, "high": 275e-9}   # upper ends of the simulated SPARK range (hw/power)
GPU_MODELS = {        # params of the GPU-side model (energy rows are projections; the 3.2 M test model
                      # would sit in GPU cache, so its HBM-based figure is not used)
    "1.1 B code LLM (projected)": 1.1e9,
    "7 B code LLM (projected)": 7e9,
}


def gpu_preds(m, data, ctx=64, step=64):
    n, out = len(data), np.zeros(len(data), dtype=np.int64)
    x = torch.from_numpy(data.astype(np.int64))
    with torch.no_grad():
        for s in range(0, n, step):
            lo = max(0, s - ctx)
            hi = min(n, s + step)
            logits, _ = m(x[lo:hi][None, :], targets=x[lo:hi][None, :])  # targets -> all positions
            out[s:hi] = logits[0, s - lo:hi - lo].argmax(-1).numpy()
    return out


def spark_run(W, data, ov):
    g = sg.Golden(W, sg.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr" if W.th is not None else "sym",
                            **ov))
    r = [g.step(int(b)) for b in data]
    return np.array([o["pred"] for o in r]), np.array([o["path"] for o in r])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bytes", type=int, default=20000)
    ap.add_argument("--spark", default=os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    ap.add_argument("--gpu", default=os.path.join(HERE, "out", "gpu_model.pt"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    torch.set_num_threads(2)
    data = tr.load_corpus(3_000_000)
    n = len(data)
    cal = data[int(n * 0.9): int(n * 0.9) + a.bytes]
    test = data[int(n * 0.95): int(n * 0.95) + a.bytes]

    ck = torch.load(a.gpu)
    m = GPT(GPTConfig(**ck["cfg"]))
    m.load_state_dict(ck["state"])
    m.eval()
    P = m.get_num_params()
    W = sg.Weights.from_npz(a.spark)

    gp = {k: gpu_preds(m, d) for k, d in (("cal", cal), ("test", test))}
    acc = lambda p, d: float(np.mean(p[:-1] == d[1:]))  # noqa: E731
    gpu_only = {k: acc(gp[k], d) for k, d in (("cal", cal), ("test", test))}
    print(f"GPU-only ({P/1e6:.2f} M params) accuracy: cal {gpu_only['cal']:.1%}  test {gpu_only['test']:.1%}", flush=True)

    # candidate SPARK settings (all programmable over the chip's UART config command)
    cands = []
    for c in (0, 1, 2, 3):
        cands.append((f"recall conf>={c}", dict(recall=1, conf_th=c, recall_mode=0), "low"))
        for t in (16, 32, 64, 128):
            cands.append((f"recall conf>={c} + exit margin>={t}",
                          dict(recall=1, conf_th=c, recall_mode=0, exit_en=1, exit_th=t), "low"))
    rows = []
    for name, ov, eff in cands:
        r = {"name": name, "cfg": ov, "effort": eff}
        for k, d in (("cal", cal), ("test", test)):
            sp, path = spark_run(W, d, ov)
            local = path != 0
            casc = np.where(local, sp, gp[k])
            ok = casc[:-1] == d[1:]
            r[k] = {"gpu_fraction": float(1 - local.mean()),
                    "accuracy": float(ok.mean()),
                    "spark_local_accuracy": float(np.mean(sp[:-1][local[:-1]] == d[1:][local[:-1]])) if local.any() else None,
                    "agree_with_gpu_only": float(np.mean(casc == gp[k])),
                    "paths": [int(np.sum(path == p)) for p in range(3)]}
        rows.append(r)
        print(f"{name:34s} cal: GPU {r['cal']['gpu_fraction']:.1%} acc {r['cal']['accuracy']:.1%} | "
              f"test: GPU {r['test']['gpu_fraction']:.1%} acc {r['test']['accuracy']:.1%} "
              f"(SPARK-local acc {r['test']['spark_local_accuracy'] or 0:.1%})", flush=True)

    # operating points chosen on the calibration slice only, then reported on the test slice
    picks = {}
    ok = [r for r in rows if r["cal"]["accuracy"] >= gpu_only["cal"]]
    if ok:
        picks["max offload, accuracy >= GPU-only"] = min(ok, key=lambda r: r["cal"]["gpu_fraction"])["name"]
    for prec in (0.80, 0.88):
        ok = [r for r in rows if (r["cal"]["spark_local_accuracy"] or 0) >= prec]
        if ok:
            picks[f"max offload, SPARK-local accuracy >= {prec:.0%}"] = min(ok, key=lambda r: r["cal"]["gpu_fraction"])["name"]

    def energy(params, gpu_frac, eff):
        params = params or P
        e_w = params * 2 * 8 * E_HBM_BIT          # weight read per GPU decode step
        e_c = 2 * params * E_FLOP                 # compute per token (always paid, KV cache)
        base = e_w + e_c
        sys_ = SPARK_J[eff] + gpu_frac * e_w + e_c
        return base, sys_

    summary = []
    for label, nm in picks.items():
        r = next(x for x in rows if x["name"] == nm)
        ent = {"operating_point": label, "setting": nm, "test": r["test"], "energy": {}}
        for gname, params in GPU_MODELS.items():
            b, s = energy(params, r["test"]["gpu_fraction"], r["effort"])
            ent["energy"][gname] = {"gpu_only_J_per_token": b, "spark_plus_gpu_J_per_token": s,
                                    "saving_x": b / s}
        summary.append(ent)
    out = {"test_bytes": len(test), "gpu_model_params": P, "gpu_only_accuracy": gpu_only,
           "constants": {"E_FLOP": E_FLOP, "E_HBM_BIT": E_HBM_BIT, "SPARK_J": SPARK_J},
           "rows": rows, "operating_points": summary}
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "cascade_results.json"), "w"), indent=1)
    for e in summary:
        print(f"\n{e['operating_point']}: {e['setting']}  GPU used for {e['test']['gpu_fraction']:.1%} of tokens, "
              f"accuracy {e['test']['accuracy']:.1%} (GPU-only {gpu_only['test']:.1%})")
        for g, v in e["energy"].items():
            print(f"   {g:40s} {v['gpu_only_J_per_token']*1e6:10.2f} uJ -> {v['spark_plus_gpu_J_per_token']*1e6:10.2f} uJ  ({v['saving_x']:.2f}x)")


if __name__ == "__main__":
    main()
