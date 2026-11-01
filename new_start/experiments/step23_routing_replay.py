#!/usr/bin/env python3
"""Step 23: expert-cache replay on open routing traces (plan and bar: new_start/step23_routing_replay_plan.md).
Streams the first N tokens of the `indices` column of FLAME-MoE-Traces layers (no full download), then replays caches of 7 and 13 routed experts per layer with offline-optimal (Belady), LRU and windowed LFU policies. Every miss counts as a read over the tier (no prefetch credit).
usage: python step23_routing_replay.py [N_TOKENS] > step23_routing_replay.log"""
import sys, numpy as np, pyarrow.parquet as pq
from huggingface_hub import HfFileSystem
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
LAYERS = [2, 4, 6, 8, 10, 12, 14, 16]; CAPS = [7, 13]; MODEL = "flame-moe-1.7b"; CKPT = "iter_11000"
fs = HfFileSystem()
def load(layer):
    p = "datasets/CMU-FLAME/FLAME-MoE-Traces/%s/actives/%s/layer_%02d.parquet" % (MODEL, CKPT, layer)
    rows = []
    with fs.open(p, "rb") as f:
        pf = pq.ParquetFile(f); got = 0
        for b in pf.iter_batches(batch_size=50000, columns=["indices"]):
            a = np.array(b.column("indices").to_pylist(), dtype=np.int16); rows.append(a); got += len(a)
            if got >= N: break
    return np.concatenate(rows)[:N]
def belady(acc, cap):
    n = len(acc); nxt = np.empty(n, dtype=np.int64); last = {}
    for i in range(n - 1, -1, -1): nxt[i] = last.get(acc[i], n + 1); last[acc[i]] = i
    cache = {}; hits = 0  # expert -> next use position
    for i in range(n):
        e = acc[i]
        if e in cache: hits += 1; cache[e] = nxt[i]
        else:
            if len(cache) >= cap: del cache[max(cache, key=cache.get)]
            cache[e] = nxt[i]
    return hits / n
def lru(acc, cap):
    cache = []; hits = 0
    for e in acc:
        if e in cache: hits += 1; cache.remove(e); cache.append(e)
        else:
            if len(cache) >= cap: cache.pop(0)
            cache.append(e)
    return hits / len(acc)
def lfu(acc, cap, win=2000):
    cnt = {}; cache = set(); hits = 0; hist = []
    for e in acc:
        if e in cache: hits += 1
        cnt[e] = cnt.get(e, 0) + 1; hist.append(e)
        if len(hist) > win: old = hist[len(hist) - win - 1]; cnt[old] -= 1
        if e not in cache:
            if len(cache) >= cap: v = min(cache, key=lambda x: cnt.get(x, 0)); cache.discard(v)
            cache.add(e)
    return hits / len(acc)
print("Step 23 expert-cache replay, %s %s, first %d tokens per layer, top-6 of 64 routed experts, every miss counted as a tier read" % (MODEL, CKPT, N))
res = {c: {"belady": [], "lru": [], "lfu": []} for c in CAPS}; usage = []
for L in LAYERS:
    idx = load(L); acc = np.sort(idx, axis=1).reshape(-1).tolist()  # per token, experts in sorted order
    top = np.bincount(idx.reshape(-1), minlength=64); share = np.sort(top)[::-1] / top.sum(); usage.append((L, share[:7].sum(), share[:13].sum()))
    line = "layer %2d: top-7 experts carry %.3f of reads, top-13 %.3f |" % (L, share[:7].sum(), share[:13].sum())
    for c in CAPS:
        b, l, f = belady(acc, c), lru(acc, c), lfu(acc, c); res[c]["belady"].append(b); res[c]["lru"].append(l); res[c]["lfu"].append(f)
        line += " cap %d: Belady %.3f LRU %.3f LFU %.3f |" % (c, b, l, f)
    print(line, flush=True)
print()
for c in CAPS:
    for pol in ("belady", "lru", "lfu"):
        v = np.array(res[c][pol]); print("cap %2d (%.2f x active) %-6s overall mean %.3f, 10th-percentile layer %.3f, min %.3f" % (c, c / 6.0, pol, v.mean(), np.percentile(v, 10), v.min()))
b = np.array(res[7]["belady"]); ok = b.mean() >= 0.82 and np.percentile(b, 10) >= 0.60
print("\nBAR (capacity 7 = 1.17 x active here, offline optimum: overall >= 0.82 and 10th-percentile layer >= 0.60): overall %.3f, p10 %.3f -> %s" % (b.mean(), np.percentile(b, 10), "PASS" if ok else "FAIL (the demand-cache route stops)"))
