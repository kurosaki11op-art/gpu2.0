"""Paired comparison of lookup-only vs hybrid (tables + 64/32 network), the way the outside critique asked:
same positions, per-byte correctness, discordant counts, and a block bootstrap (dependent bytes are resampled in blocks) for the
accuracy difference. Also: how often the network decides, and who is right when it does.
Hybrid modes: 0 = a table hit answers directly (network only on misses); 2 = the network arbitrates (it overrides a table hit when
its main-head margin is >= arb_th). Both use the hysteresis table update, exit head off.
Documents: 20,000-byte slices of code (one corpus) and of four books. usage: python paired_stats.py <book dir>"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nontext_probe as npb, hash_study as hs  # noqa
g1 = npb.g1; g1.H, g1.D = 64, 32
rp = npb.rp
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
docs = {"code": (bytes(Z["test_text"]), "out_h64_d32_full")}
for b in npb.BOOKS:
    raw = np.frombuffer(open(os.path.join(sys.argv[1], b), "rb").read(), dtype=np.uint8); s0 = int(len(raw) * 0.4)
    docs[b.split(".")[0]] = (raw[s0:s0 + 20000].tobytes(), "out_prose_64")
weights = {}


def hybrid(text, wdir, mode):
    if wdir not in weights:
        weights[wdir] = g1.Weights.from_npz(os.path.join(HERE, "..", "train", wdir, "spark_v0_model.npz"))
    cfg = g1.Cfg(**{**npb.CFG, "recall_mode": mode, "exit_en": 0})
    g = rp.Policy(weights[wdir], cfg, tb=12, lut=npb.lut, update="hyst")
    outs = [g.step(b) for b in text]
    return np.array([o["pred"] for o in outs]), np.array([o["path"] for o in outs])


rng = np.random.default_rng(0)


def block_boot(d, block=250, reps=2000):
    n = len(d); nb = n // block; d = d[:nb * block].reshape(nb, block).mean(1)
    m = [d[rng.integers(0, nb, nb)].mean() for _ in range(reps)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


rows = {}; pool = {0: [], 2: []}
for name, (text, wdir) in docs.items():
    t = np.frombuffer(text, dtype=np.uint8); tt = t[1:]
    lk = hs.lookup(t, hs.h_crc)[0][:-1]; lk_ok = (lk == tt)
    row = {"lookup_acc": float(lk_ok.mean())}
    for mode in (0, 2):
        p, path = hybrid(text, wdir, mode); p = p[:-1]; path = path[:-1]; ok = (p == tt)
        net = path == 0
        row[f"mode{mode}"] = {"acc": float(ok.mean()), "diff_vs_lookup": float(ok.mean() - lk_ok.mean()),
                              "hybrid_right_lookup_wrong": float((ok & ~lk_ok).mean()), "lookup_right_hybrid_wrong": float((~ok & lk_ok).mean()),
                              "network_decides_frac": float(net.mean()),
                              "acc_when_network_decides": float(ok[net].mean()) if net.any() else None,
                              "lookup_acc_on_same_bytes": float(lk_ok[net].mean()) if net.any() else None}
        pool[mode].append(ok.astype(float) - lk_ok.astype(float))
    rows[name] = row
    print(name, json.dumps({k: (round(v, 4) if isinstance(v, float) else {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()}) for k, v in row.items()}), flush=True)
out = {"per_doc": rows}
for mode in (0, 2):
    d = np.concatenate(pool[mode]); lo, hi = block_boot(d)
    out[f"pooled_mode{mode}"] = {"mean_diff": float(d.mean()), "ci95_block_bootstrap": [lo, hi], "n_bytes": int(len(d)), "docs": len(docs)}
    print(f"POOLED mode {mode}: hybrid - lookup = {d.mean() * 100:+.2f} points, 95% CI [{lo * 100:+.2f}, {hi * 100:+.2f}] (block bootstrap, 250-byte blocks, {len(d)} bytes, {len(docs)} documents)")
json.dump(out, open(os.path.join(HERE, "..", "results", "paired_stats.json"), "w"), indent=1)
