"""Multi-scale recall (hippocampus with several context lengths) + network arbitration.
Uses feats npz (seq, main logits lm computed with full state every token = effort 1/2 semantics)."""
import sys, numpy as np

def H(x, bits, salt):
    return (((x * 0x9E3779B1) ^ (salt * 0x85EBCA6B)) & 0xFFFFFFFF) >> (32 - bits)

def recall(seq, orders, bits=10, conf_th=0, n=None):
    n = n or len(seq) - 1
    """direct-mapped table; entry = (tag, value, conf). Predict from longest order that hits."""
    tag = np.full(1 << bits, -1, np.int64); val = np.zeros(1 << bits, np.int64); conf = np.zeros(1 << bits, np.int64)
    pred = np.full(n, -1); pconf = np.zeros(n, int); porder = np.zeros(n, int)
    for t in range(n):
        # update with the byte that just arrived (seq[t]) for contexts ending at t-1
        for k in orders:
            if t - k < 0: continue
            ctx = 0
            for i in range(k): ctx = (ctx << 8) | int(seq[t - 1 - i])
            key = (ctx << 3) | k; s = H(ctx & 0xFFFFFFFF ^ (ctx >> 32), bits, k)
            if tag[s] == key:
                if val[s] == seq[t]: conf[s] = min(conf[s] + 1, 3)
                else: val[s] = seq[t]; conf[s] = 0
            else: tag[s] = key; val[s] = seq[t]; conf[s] = 0
        # predict next byte seq[t+1] from contexts ending at t
        for k in sorted(orders, reverse=True):
            if t + 1 - k < 0: continue
            ctx = 0
            for i in range(k): ctx = (ctx << 8) | int(seq[t - i])
            key = (ctx << 3) | k; s = H(ctx & 0xFFFFFFFF ^ (ctx >> 32), bits, k)
            if tag[s] == key and conf[s] >= conf_th:
                pred[t] = val[s]; pconf[t] = conf[s]; porder[t] = k; break
    return pred, pconf, porder

