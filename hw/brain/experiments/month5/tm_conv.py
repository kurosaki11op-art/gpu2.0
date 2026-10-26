"""26 Oct 2026, SIMULATED, Fashion-MNIST, one seed. Piece 5: WEIGHT SHARING ACROSS POSITIONS. The same local clause learner as tm_faithful.py, but a clause reads a small WINDOW of L's detector map (W x W cells of the 6 x 6 grid, all 4 channels x 32 detectors per cell = W*W*128 bits, plus row/column bits) and the SAME clause is tried at every window position; it fires if it matches at any position (as in the convolutional Tsetlin machine; no matrix, no multiply, no backprop). Feedback is applied at a randomly chosen matching position. A clause carries only its included literals (shared across positions).
env: C clauses per class, TT, SS, WIN (window width, default 3), BUDGET, RESET."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, CL
from numba import njit, prange
E_ = lambda k, d: type(d)(os.environ.get(k, d))
C = E_("C", 200); T = E_("TT", 30); S = E_("SS", 3.0); WIN = E_("WIN", 3); BUDGET = E_("BUDGET", 480); LMAX = E_("LMAX", 64); NST = 100
RAW = E_("RAW", 0); ST = E_("ST", 1); GH = 28 if RAW else 6; FB = 2 if RAW else 128
def grid(c): n = len(c); return np.ascontiguousarray(c.reshape(n, 4, 6, 6, 32).transpose(0, 2, 3, 1, 4).reshape(n, 6, 6, 128)).astype(np.uint8)   # code bit = channel*1152 + (i*6+j)*32 + f
if RAW:
    from shirt_new_methods_setup import xtr, xte
    def rawgrid(x): im = x.reshape(-1, 28, 28); return np.stack([(im > 85), (im > 170)], -1).astype(np.uint8)
    G, Gt = rawgrid(xtr), rawgrid(xte)
else: G, Gt = grid(ctr), grid(cte)
y = ytr.astype(np.int64)
NW = (GH - WIN) // ST + 1; NPOS = NW * NW; NP = WIN * WIN * FB + 2 * NW; NL = 2 * NP
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_conv_state_w%d%s.npz" % (WIN, "_raw" if RAW else "")
@njit
def pbit(g, p, k):                                                                                    # bit k of the window at position p of image g
    pi = p // NW; pj = p % NW
    if k < WIN * WIN * FB:
        c = k // FB; return g[pi * ST + c // WIN, pj * ST + c % WIN, k % FB]
    k -= WIN * WIN * FB
    return 1 if (k < NW and pi == k) or (k >= NW and pj == k - NW) else 0
@njit
def matches(cl, g, p, inc_list, inc_n):
    for t in range(inc_n[cl]):
        lit = inc_list[cl, t]
        if lit < NP:
            if pbit(g, p, lit) == 0: return False
        elif pbit(g, p, lit - NP) == 1: return False
    return True
@njit
def fires(cl, g, inc_list, inc_n, train):
    if inc_n[cl] == 0: return 1 if train else 0
    for p in range(NPOS):
        if matches(cl, g, p, inc_list, inc_n): return 1
    return 0
@njit
def class_sum(c, g, inc_list, inc_n, train, outs):
    v = 0
    for j in range(C):
        o = fires(c * C + j, g, inc_list, inc_n, train); outs[j] = o
        if o: v += 1 if j % 2 == 0 else -1
    return max(-T, min(T, v))
@njit(parallel=True)
def feedback(c, g, state, inc_list, inc_n, outs, v, positive_target, seeds):
    p_ = (T - v) / (2.0 * T) if positive_target else (T + v) / (2.0 * T)
    for j in prange(C):
        np.random.seed(seeds[j])
        if np.random.random() > p_: continue
        cl = c * C + j; type1 = ((j % 2 == 0) == positive_target); pos = 0
        if outs[j] == 1 and inc_n[cl] > 0:                                                           # pick a random matching position (reservoir)
            cnt = 0
            for q in range(NPOS):
                if matches(cl, g, q, inc_list, inc_n):
                    cnt += 1
                    if np.random.randint(cnt) == 0: pos = q
        elif outs[j] == 1: pos = np.random.randint(NPOS)
        if type1:
            if outs[j] == 1:
                for k in range(NL):
                    lt = pbit(g, pos, k) == 1 if k < NP else pbit(g, pos, k - NP) == 0
                    if lt:
                        if np.random.random() < (S - 1.0) / S and state[cl, k] < 2 * NST: state[cl, k] += 1
                    elif np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
            else:
                for k in range(NL):
                    if np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
        elif outs[j] == 1:
            for k in range(NL):
                lt = pbit(g, pos, k) == 1 if k < NP else pbit(g, pos, k - NP) == 0
                if (not lt) and state[cl, k] <= NST: state[cl, k] += 1
        n = 0
        for k in range(NL):
            if state[cl, k] > NST and n < LMAX: inc_list[cl, n] = k; n += 1
        inc_n[cl] = n
@njit
def train_epoch(G, y, order, state, inc_list, inc_n, seed, start, count):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); done = 0
    for ii in range(start, min(start + count, len(order))):
        i = order[ii]; g = G[i]; c = y[i]
        v = class_sum(c, g, inc_list, inc_n, True, outs); feedback(c, g, state, inc_list, inc_n, outs, v, True, np.random.randint(0, 2 ** 30, C))
        o = (c + 1 + np.random.randint(9)) % 10
        v2 = class_sum(o, g, inc_list, inc_n, True, outs2); feedback(o, g, state, inc_list, inc_n, outs2, v2, False, np.random.randint(0, 2 ** 30, C)); done += 1
    return done
@njit(parallel=True)
def predict(Gt, inc_list, inc_n):
    out = np.zeros((len(Gt), 10), np.int32)
    for i in prange(len(Gt)):
        outs = np.zeros(C, np.int8)
        for c in range(10): out[i, c] = class_sum(c, Gt[i], inc_list, inc_n, False, outs)
    return out
def fire_bits(Gx, inc_list, inc_n):
    return _fb(Gx, inc_list, inc_n)
@njit(parallel=True)
def _fb(Gx, inc_list, inc_n):
    out = np.zeros((len(Gx), len(inc_n)), np.uint8)
    for i in prange(len(Gx)):
        for cl in range(len(inc_n)): out[i, cl] = fires(cl, Gx[i], inc_list, inc_n, False)
    return out
if __name__ == "__main__":
    if os.environ.get("RESET", "0") == "0" and os.path.exists(CK): z = np.load(CK); state, inc_list, inc_n, ep, pos = z["state"], z["inc_list"], z["inc_n"], int(z["ep"]), int(z["pos"])
    else: state = np.full((10 * C, NL), NST, np.uint8); inc_list = np.zeros((10 * C, LMAX), np.int32); inc_n = np.zeros(10 * C, np.int32); ep = 0; pos = 0
    t0 = time.time()
    def report(tag):
        sc = predict(Gt, inc_list, inc_n).astype(np.float32); p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
        print("[%4.0fs] %s: test acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | mean included literals per clause %.1f" % (time.time() - t0, tag, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, inc_n.mean()), flush=True)
    while time.time() - t0 < BUDGET:
        order = np.random.RandomState(100 + ep).permutation(len(G)); n = train_epoch(G, y, order, state, inc_list, inc_n, 1000 + ep * 7 + pos, pos, 2000); pos += n
        if pos >= len(G): pos = 0; ep += 1; report("after epoch %d" % ep)
        elif pos % 10000 == 0: report("  epoch %d, %d images" % (ep, pos))
    np.savez(CK, state=state, inc_list=inc_list, inc_n=inc_n, ep=ep, pos=pos); report("saved (epoch %d, position %d)" % (ep, pos))
