#!/usr/bin/env python3
"""cortex_board_top.v over UART vs the integer model: every reply byte must match.
Session: seed lanes, clear, learn classes 0/1, then 2 with dreams of 0/1, predictions. usage: python check_cortex_board.py DATA_DIR"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(int), yte.astype(int); NB = ctr.shape[1]
m = CortexInt(NB); buf = np.zeros(NB, np.int32)
cmds, replies = [], []
def cmd(b, rep): cmds.append(bytes(b)); replies.append(bytes(rep))
seeds = m.rng.copy()
cmd([0xE0], [0x5A])
cmd([0x53] + [x for s in seeds for x in int(s).to_bytes(4, "little")], [0x53])
cmd([0x43], [0x43])
r = np.random.RandomState(0)
def learn(c, idx):
    a = np.nonzero(ctr[idx])[0].astype(np.int32)
    _count(m.on, m.n, a, len(a), c, m.top); u = _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax)
    cmd([0x4C, c, len(a) & 255, len(a) >> 8] + [x for v in a for x in (int(v) & 255, int(v) >> 8)], [u])
for c in (0, 1):
    cmd([0x4B, c], [0x4B]); m.known[c] = True
for idx in r.choice(np.where(ytr < 2)[0], 30, replace=False):
    learn(int(ytr[idx]), idx)
cmd([0x4B, 2], [0x4B]); m.known[2] = True
for idx in r.choice(np.where(ytr == 2)[0], 15, replace=False):
    learn(2, idx)
    for c in (0, 1):
        k = _dream(m.on, m.n, c, m.rng, buf); u = _practise(m.W, buf, k, c, m.known, m.margin, m.cmax)
        cmd([0x44, c], [k & 255, k >> 8, u])
# ---- image path: detectors loaded once, then raw 28x28 images; the chip encodes them itself ----
from feature_layer import Features  # noqa
xtr, _, xte, _ = load(D, "mnist")
fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
words = [sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)]
cmd([0x54] + [b for w in words for b in w.to_bytes(4, "little")], [0x54])
cmd([0x4B, 3], [0x4B]); m.known[3] = True
for idx in r.choice(np.where(ytr == 3)[0], 6, replace=False):
    a = np.nonzero(np.concatenate([f.encode(xtr[idx:idx + 1]) for f in fes], 1)[0])[0].astype(np.int32)
    _count(m.on, m.n, a, len(a), 3, m.top); u = _practise(m.W, a, len(a), 3, m.known, m.margin, m.cmax)
    cmd([0x49, 3] + list(int(v) for v in xtr[idx]), [u])
for t in r.choice(np.where(yte < 4)[0], 6, replace=False):
    a = np.nonzero(np.concatenate([f.encode(xte[t:t + 1]) for f in fes], 1)[0])[0]
    s = np.array([m.W[c, a].astype(int).sum() if m.known[c] else -(1 << 40) for c in range(10)])
    cmd([0x49, 0xFF] + list(int(v) for v in xte[t]), [int(s.argmax())])
for t in r.choice(np.where(yte < 3)[0], 20, replace=False):
    a = np.nonzero(cte[t])[0]
    s = np.array([m.W[c, a].astype(int).sum() if m.known[c] else -(1 << 40) for c in range(10)])
    cmd([0x50, len(a) & 255, len(a) >> 8] + [x for v in a for x in (int(v) & 255, int(v) >> 8)], [int(s.argmax())])
# ---- memory transfer: read counts and words, write words and counts, then predict with the changed memory ----
def wordbytes(b):
    w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (10 * c) for c in range(10))
    return w.to_bytes(7, "little") + cw.to_bytes(13, "little")
def nbytes():
    nv = sum(int(m.n[c]) << (10 * c) for c in range(10)); kv = sum(1 << c for c in range(10) if m.known[c])
    return nv.to_bytes(13, "little") + kv.to_bytes(2, "little")
cmd([0x4E], list(nbytes()))
for b in (0, 5, 777, 4607):
    cmd([0x52, b & 255, b >> 8], list(wordbytes(b)))
for b in (3, 4000):
    w = r.randint(0, 1 << 30, size=2); wv = (int(w[0]) | (int(w[1]) << 30)) & ((1 << 50) - 1)
    cv = sum(int(v) << (10 * c) for c, v in enumerate(r.randint(0, 200, size=10)))
    for c in range(10):
        f = (wv >> (5 * c)) & 0x1F; m.W[c, b] = f - 32 if f >= 16 else f; m.on[c, b] = (cv >> (10 * c)) & 1023
    cmd([0x57, b & 255, b >> 8] + list(wv.to_bytes(7, "little") + cv.to_bytes(13, "little")), [0x57])
    cmd([0x52, b & 255, b >> 8], list(wordbytes(b)))
newn = r.randint(1, 900, size=10); m.n[:] = newn; m.known[:] = True
nv = sum(int(v) << (10 * c) for c, v in enumerate(newn))
cmd([0x4D] + list(nv.to_bytes(13, "little") + (1023).to_bytes(2, "little")), [0x4D])
cmd([0x4E], list(nbytes()))
for t in r.choice(len(yte), 5, replace=False):
    a = np.nonzero(cte[t])[0]
    s = np.array([m.W[c, a].astype(int).sum() for c in range(10)])
    cmd([0x50, len(a) & 255, len(a) >> 8] + [x for v in a for x in (int(v) & 255, int(v) >> 8)], [int(s.argmax())])
allb = b"".join(cmds)
open(os.path.join(HERE, "in_cortex.hex"), "w").write("\n".join("%02x" % x for x in allb) + "\n")
open(os.path.join(HERE, "in_cortex_n.hex"), "w").write("\n".join("%04x\n%04x" % (len(c), len(rp)) for c, rp in zip(cmds, replies)) + "\n")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/cxb.vvp", f"-Ptb_cortex_board.NBYTES={len(allb) + 4}",
                "-I", "../rtl/cortex", "cortex_board_top.v", "uart_rx.v", "uart_tx.v", "../rtl/cortex/cortex_core.v",
                "../rtl/cortex/cortex_encoder.v", "tb_cortex_board.v"],
               cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/cxb.vvp"], cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-400:])
got = bytes(int(x, 16) for x in open(os.path.join(HERE, "out_cortex_board.txt")).read().split())
exp = b"".join(replies)
bad = sum(a != b for a, b in zip(got, exp)) + abs(len(got) - len(exp))
print(f"{len(cmds)} commands, {len(allb)} bytes sent, reply bytes expected {len(exp)} got {len(got)}, mismatches {bad}")
print("PASS" if bad == 0 else "FAIL")
