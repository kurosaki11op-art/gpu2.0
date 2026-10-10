"""On-chip learning prototype: error-driven (three-factor) plasticity on the main head.
Pre-synaptic spike (s1_j) x post-synaptic error (target vs predicted) -> int4 weight step."""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../golden'); import spark_golden as sg
F = np.load(sys.argv[1]); W0 = sg.Weights.from_npz(sys.argv[2]).w[3].astype(np.int32)
split = sys.argv[3] if len(sys.argv) > 3 else 'cal'
seq, S1 = F[split + '_seq'], F[split + '_s1'].astype(np.int32)

def run(rule, p=1.0, smin=1, margin=0, seed=1, n=None, step=1, wmax=7):
    W = W0.copy(); rng = np.random.default_rng(seed)
    n = n or len(seq) - 1; ok = np.zeros(n, bool)
    for t in range(n):
        s = S1[t]; lg = W @ s; y = seq[t + 1]
        pr = int(np.argmax(lg)); ok[t] = pr == y
        if rule == 'none': continue
        srt = np.partition(lg, -2)
        if pr != y or (lg[y] - np.partition(lg, -2)[-2] if pr == y else 0) < margin:
            if rng.random() > p: continue
            act = s >= smin
            if pr != y:
                W[y, act] = np.minimum(W[y, act] + step, wmax)
                W[pr, act] = np.maximum(W[pr, act] - step, -8)
            else:  # correct but low margin: strengthen target only
                W[y, act] = np.minimum(W[y, act] + step, wmax)
    return ok

base = run('none')
print(f'no learning: {base.mean():.1%}  first2k {base[:2000].mean():.1%}  last half {base[len(base)//2:].mean():.1%}')
for p in [1.0, 0.3, 0.1, 0.03]:
    for smin in [1, 3]:
        ok = run('perc', p=p, smin=smin)
        print(f'perceptron p={p} smin={smin}: {ok.mean():.1%}  first2k {ok[:2000].mean():.1%}  last half {ok[len(ok)//2:].mean():.1%}', flush=True)
