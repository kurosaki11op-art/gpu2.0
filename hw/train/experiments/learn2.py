"""Brain-like on-chip learning variants on the main head (S1 states are independent of the head).
 bias : intrinsic plasticity - per-output bias b[v] (int), +step on target, -step on wrong winner, slow decay
 fast : fast synapses F (int8) beside fixed slow weights W; logits = W@s + (F@s >> fs); F decays (forgetting)
"""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../golden'); import spark_golden as sg
F_ = np.load(sys.argv[1]); WM = sg.Weights.from_npz(sys.argv[2]).w[3].astype(np.int64)
split = sys.argv[3]
seq, S1 = F_[split + '_seq'].astype(np.int64), F_[split + '_s1'].astype(np.int64)
n = len(seq) - 1; y = seq[1:]
base = (S1 @ WM.T)

def bias(step, dec_every, bmax=2048):
    b = np.zeros(256, np.int64); ok = np.zeros(n, bool)
    for t in range(n):
        lg = base[t] + b; p = int(lg.argmax()); ok[t] = p == y[t]
        if p != y[t]:
            b[y[t]] = min(b[y[t]] + step, bmax); b[p] = max(b[p] - step, -bmax)
        if dec_every and t % dec_every == 0: b -= b >> 4
    return ok

def fast(fs, dec_every, fmax=127, step=1, only_err=True):
    Fw = np.zeros((256, S1.shape[1]), np.int64); ok = np.zeros(n, bool)
    for t in range(n):
        s = S1[t]; lg = base[t] + ((Fw @ s) >> fs); p = int(lg.argmax()); ok[t] = p == y[t]
        if p != y[t] or not only_err:
            act = s > 0
            Fw[y[t], act] = np.minimum(Fw[y[t], act] + step * s[act], fmax)
            if p != y[t]: Fw[p, act] = np.maximum(Fw[p, act] - step * s[act], -fmax - 1)
        if dec_every and t % dec_every == 0: Fw -= Fw >> 3
    return ok

r = lambda ok: f'{ok.mean():.1%} (last half {ok[n // 2:].mean():.1%})'
print('no learning', r(np.argmax(base, 1)[:n] == y))
for step in (8, 32, 128):
    for de in (0, 64, 512):
        print(f'bias step={step} decay/{de}:', r(bias(step, de)), flush=True)
for fs in (0, 2, 4):
    for de in (0, 256, 2048):
        print(f'fast synapses shift={fs} decay/{de}:', r(fast(fs, de)), flush=True)
