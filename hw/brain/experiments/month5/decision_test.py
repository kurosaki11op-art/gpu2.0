"""(env SLOW=1: CortexSlow, slow table, 18 Oct 2026; env STRIDE1=1: images with detectors at stride 1 and pool 4, 19 Oct 2026.) Final numbers with every adopted option together (16 Oct 2026): margin 32 (default now), word alignment lead 6 for
sound, LOOK AGAIN at test time (images: the picture + 4 one-pixel shifts with the centre counted twice; sound: the word
aligned at start frames 5, 6, 6, 7), IMPRINT + short sleep irrelevant here (no few-shot). Exact integer chip model, 5
seeds, all at once and 5 stages, plus the single-view (no LOOK AGAIN) numbers. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
SLOW = True
S1 = True      # images: detectors at stride 1, pool 4 (same 4,608-bit code, finer winner grid)
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    import cochlea_int
    from feature_layer import Features
    f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
    ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
    xtr = cochlea_int.align_word(P0[~te], 6)
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    ctr = enc(xtr); views = {L: enc(cochlea_int.align_word(P0[te], L)).astype(np.int32) for L in (5, 6, 7)}
    centre, extra = views[6], [views[5], views[6], views[7]]          # views 5, 6, 6, 7 = centre + [5, 6, 7]
else:
    from feature_layer import Features
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    
    CH = (50, 150, ("on", 8), ("off", 8))
    if S1:
        import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
    fes = [Features(32, thr=c, pool=4 if S1 else 2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    X = xte.reshape(len(xte), 28, 28)

    def shifted(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)

    if S1:
        ctr = enc(xtr)
    centre = enc(xte).astype(np.int32); extra = [shifted(-1, 0), shifted(1, 0), shifted(0, -1), shifted(0, 1)]


import torch, torch.nn as nn, time
torch.set_num_threads(4); torch.manual_seed(0)
"""Decision test: redesign L (a second layer on L's own code) or build a second model? (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed.)
Upper bounds for 'a hidden layer on top of L's 4,608-bit detector code': (a) float ReLU hidden layer trained by backprop (best case, not deployable); (b) binary hidden units (sign activation, straight-through) = what a lookup/gate chip could hold; both read by a linear layer.
Compared with L's counting table on the same code and with the CNN ruler (91.1 to 91.7 overall, Shirt AP 0.84)."""
CL = np.array([0, 2, 4, 6]); X = torch.tensor(ctr, dtype=torch.float32); Xt = torch.tensor(centre, dtype=torch.float32); Y = torch.tensor(ytr)
def report(tag, sc, t0):
    sc = sc.numpy(); p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    print("%-52s accuracy %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | %.0fs" % (tag, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum(), time.time() - t0), flush=True)
class SignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x): ctx.save_for_backward(x); return (x > 0).float()
    @staticmethod
    def backward(ctx, g): (x,) = ctx.saved_tensors; return g * (x.abs() < 1).float()
def run(tag, H, binary, epochs):
    t0 = time.time(); torch.manual_seed(0); l1 = nn.Linear(X.shape[1], H); l2 = nn.Linear(H, 10); params = list(l1.parameters()) + list(l2.parameters()); opt = torch.optim.Adam(params, 1e-3)
    f = (lambda x: l2(SignSTE.apply(l1(x)))) if binary else (lambda x: l2(torch.relu(l1(x))))
    for ep in range(epochs):
        pm = torch.randperm(len(X))
        for i in range(0, len(X), 256): b = pm[i:i + 256]; loss = nn.functional.cross_entropy(f(X[b]), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): report(tag, f(Xt), t0)
m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel]); report("L counting table on the code (reference)", torch.tensor((centre @ m.S.astype(np.int32).T).astype(np.float32)), time.time())
which = os.environ.get("WHICH", "float")
if which == "float": run("hidden 512, float ReLU, backprop (upper bound)", 512, False, 8)
else: run("hidden 512, BINARY units (sign, STE) (deployable)", 512, True, 8)
