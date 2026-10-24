"""FPTM-style rich input code with L's counting readout (24 Oct 2026, SIMULATED, one seed). Encoding copied from the Fuzzy-Pattern Tsetlin Machine as read in the notes (arXiv 2508.08350 and its code):
raw pixel 4-level thermometer (x>0, >q25, >q50, >q75 of nonzero pixels) + 8 fixed edge maps (separable Sobel-type x kernels of size 3, 5, 7 and a 3x3 line detector, each also rotated 90 degrees),
every edge map coded in 9 sign-split quantile bits (positive side >0, q25, q34, q50, q75; negative side mirrored, 4 bits) = 76 maps x 784 = 59,584 bits per image. Only compares, adds, shifts and a few small constants.
Learner: L's counting table (slow-table integer model). Tests: (a) raw 4-bit code alone, (b) full code, (c) edge maps only, trained on N images (env NTRAIN, default 30000) and tested on all 10,000.
usage: python fptm_code.py DATA_DIR"""
import sys, os, time, numpy as np, torch
sys.path.insert(0, "/home/user/gpu2.0/hw/brain"); from cortex_core import load; from cortex_slow import CortexSlow
torch.set_num_threads(4); D = sys.argv[1]; NTR = int(os.environ.get("NTRAIN", 30000))
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); xtr, ytr = xtr[:NTR], ytr[:NTR]
sm = {3: [1, 2, 1], 5: [1, 4, 6, 4, 1], 7: [1, 6, 15, 20, 15, 6, 1]}; dv = {3: [-1, 0, 1], 5: [-1, -2, 0, 2, 1], 7: [-1, -4, -5, 0, 5, 4, 1]}
kers = [torch.tensor(np.outer(sm[k], dv[k]), dtype=torch.float32) for k in (3, 5, 7)]               # smoothing (rows) x derivative (columns) = x-gradient kernel
kers.append(torch.tensor([[-1, -1, -1], [2, 2, 2], [-1, -1, -1]], dtype=torch.float32))              # 3x3 line detector
kers += [k.t().contiguous() for k in kers]                                                           # rotated 90 degrees = y orientation
def responses(x):                                                                                    # (N, 8, 28, 28) float
    t = torch.tensor(x.reshape(-1, 1, 28, 28), dtype=torch.float32); out = []
    for k in kers: out.append(torch.nn.functional.conv2d(t, k[None, None], padding=k.shape[0] // 2))
    return torch.cat(out, 1)
def quants(v, pos):                                                                                  # global training-set quantiles of the nonzero positive (or |negative|) responses
    v = v[v > 0] if pos else (-v[v < 0]); v = v[torch.randperm(len(v))[:2000000]]; return [float(torch.quantile(v, q)) for q in (0.25, 0.34, 0.50, 0.75)]
t0 = time.time(); Rtr = responses(xtr); Rte = responses(xte)
Q = [(quants(Rtr[:, m], True), quants(Rtr[:, m], False)) for m in range(8)]
px = xtr[xtr > 0]; qpx = [float(np.percentile(px, q)) for q in (25, 50, 75)]
def raw_bits(x): return np.stack([(x > 0), (x > qpx[0]), (x > qpx[1]), (x > qpx[2])], 1).reshape(len(x), -1).astype(np.uint8)
def edge_bits(R):
    out = []
    for m in range(8):
        r = R[:, m].reshape(len(R), -1); qp, qn = Q[m]
        out += [(r > 0), (r > qp[0]), (r > qp[1]), (r > qp[2]), (r > qp[3]), (r < -qn[0]), (r < -qn[1]), (r < -qn[2]), (r < -qn[3])]
    return torch.stack(out, 1).reshape(len(R), -1).numpy().astype(np.uint8)
print("encoding done %.0fs" % (time.time() - t0), flush=True)
def run(tag, Ctr, Cte):
    t1 = time.time(); m = CortexSlow(Ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(Ctr[sel], ytr[sel])
    S = m.S.astype(np.int32); p = np.concatenate([(Cte[i:i + 1000].astype(np.int32) @ S.T).argmax(1) for i in range(0, len(Cte), 1000)])
    print("%-34s bits %6d | active/image %.0f | accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | table %.0f KB (8 bit), %.0f KB (2 bit) | %.0fs" % (tag, Ctr.shape[1], Cte.sum(1).mean(), (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), S.size / 1024, S.size / 4 / 1024, time.time() - t1), flush=True)
a_tr, a_te = raw_bits(xtr), raw_bits(xte); run("raw 4-level thermometer only", a_tr, a_te)
e_tr = np.concatenate([edge_bits(Rtr[i:i + 2000]) for i in range(0, len(Rtr), 2000)]); e_te = np.concatenate([edge_bits(Rte[i:i + 2000]) for i in range(0, len(Rte), 2000)])
run("edge maps only (72 bits/pixel)", e_tr, e_te)
run("FPTM code (raw + edges, 76 maps)", np.concatenate([a_tr, e_tr], 1), np.concatenate([a_te, e_te], 1))
