"""Categories from two senses with no labels (20 Oct 2026) SIMULATED. A seen digit and a heard clip of the same digit occur together (different instances); NO label is used to form the groups. 10 groups are formed by competitive learning on binary codes (k-means by overlap / mean template, k-means++ start, 6 restarts) on:
  picture alone, sound alone, both senses joined (one code = picture bits + sound bits).
Scored with the true labels ONLY to measure: cluster purity, and the accuracy of a picture learner (the chip's counting table, one pass) trained on the group names after the groups are named by ONE label per group (10 labels in total, majority of a handful of labelled members); test = MNIST test pictures.
usage: DATA_DIR SUBSET_DIR (env SET = fsdd | sc)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int, detector_learn, cross_modal
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
D, ROOT = sys.argv[1], sys.argv[2]; SET = os.environ.get("SET", "fsdd"); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = int(os.environ.get('SEEDS', 3)); K = 10
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); venc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = venc(xtr), venc(xte)
CHS = (50, 110, 170, ("on", 8))
if SET == "fsdd":
    z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; train_c = spk != spk.max()
else:
    WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]; files, sy, spk = [], [], []
    for wi, w in enumerate(WORDS):
        for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); sy.append(wi); spk.append(int(f.split("_")[0], 16))
    sy = np.array(sy); grp = np.array(spk) % 5; X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)
    S = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(X), 500)]); train_c = grp >= 1
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); sfs = [SoundFeatures(32, c, 3, 3, 1, 1, 4, 4).fit(pic[train_c][:12000]) for c in CHS]; A = np.concatenate([f.encode(pic) for f in sfs], 1); tr_i = np.where(train_c)[0]


def kmeans(X, k, seed, iters=25, restarts=int(os.environ.get('RESTARTS', 6))):
    """competitive learning on binary codes: assign to the template with the best overlap score (x . c - |c|^2 / 2), templates = member means; best of several restarts by total score"""
    X = X.astype(np.float32); best = (-1e18, None); g = np.random.RandomState(seed)
    for _ in range(restarts):
        c = [X[g.randint(len(X))]]                                                    # k-means++ start
        for _k in range(1, k):
            d = np.min([((X - ci) ** 2).sum(1) for ci in c], 0); c.append(X[g.choice(len(X), p=d / d.sum())])
        c = np.stack(c)
        for _i in range(iters):
            sc = X @ c.T - 0.5 * (c * c).sum(1)[None, :]; a = sc.argmax(1)
            for j in range(k):
                if (a == j).any(): c[j] = X[a == j].mean(0)
        sc = X @ c.T - 0.5 * (c * c).sum(1)[None, :]; tot = float(sc.max(1).sum())
        if tot > best[0]: best = (tot, sc.argmax(1))
    return best[1]


def purity(a, y): return float(sum(np.bincount(y[a == j], minlength=10).max() for j in range(K) if (a == j).any()) / len(y))


R = {}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); heard = A[np.array([r.choice(tr_i[sy[tr_i] == d]) for d in ytr])]; views = {"picture alone": vtr, "sound alone": heard, "both senses joined": np.concatenate([vtr, heard], 1)}
    for name, code in views.items():
        a = kmeans(code, K, seed); R.setdefault(name + " | purity", []).append(purity(a, ytr))
        nm = np.zeros(K, np.int64)
        for j in range(K):                                                            # name each group by ONE label: the majority of 5 randomly chosen labelled members (10 labels in total)
            mem = np.where(a == j)[0]; nm[j] = np.bincount(ytr[r.choice(mem, min(5, len(mem)), replace=False)], minlength=10).argmax() if len(mem) else 0
        names = nm[a]; R.setdefault(name + " | names right", []).append(float((names == ytr).mean()))
        m = cross_modal.fit(vtr, names, seed); R.setdefault(name + " | picture learner on the group names (10 labels in total)", []).append(float((m.predict(vte) == yte).mean()))
        mc, labc = cross_modal.learn_picture(vtr, names, rounds=2, seed=seed); R.setdefault(name + " | ... and the names cleaned in sleep (neighbour pooling)", []).append(float((mc.predict(vte) == yte).mean())); R.setdefault(name + " | ... cleaned names right", []).append(float((labc == ytr).mean()))
    R.setdefault("picture learner, all true labels (reference)", []).append(float((cross_modal.fit(vtr, ytr, seed).predict(vte) == yte).mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
print("set", SET)
for k, v in R.items(): print("%-84s %.4f" % (k, np.mean(v)), flush=True)
