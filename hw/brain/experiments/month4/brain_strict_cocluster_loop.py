"""Label-free categories, the complete loop (20 Oct 2026) SIMULATED. Pictures and sounds of the same digit occur together; no label forms the groups.
  1. groups: competitive learning (k-means by overlap) on the joined code (picture bits + sound bits)
  2. names: each group is named by ONE label (majority of 5 labelled members): 10 labels in total
  3. loop (sleep consolidation), ROUNDS times: a joint table learns the pairs under the current names; it names every pair again with BOTH senses (its own scores plus the scores of the K nearest buffered pairs, bufferes of 256: cross_modal.clean_names); repeat
  4. the picture learner (chip counting table, one pass) is trained on the final names; test = MNIST test pictures (picture only), and the joint table is tested with both senses on held-out pairs.
Reported per round: names right (true labels only to score). Reference: all true labels. usage: DATA_DIR SUBSET_DIR (env SET = fsdd | sc, SEEDS, ROUNDS, RESTARTS)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int, detector_learn, cross_modal
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
D, ROOT = sys.argv[1], sys.argv[2]; SET = os.environ.get("SET", "fsdd"); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = int(os.environ.get("SEEDS", 2)); ROUNDS = int(os.environ.get("ROUNDS", 3)); RESTARTS = int(os.environ.get("RESTARTS", 3)); K = 10
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); venc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = venc(xtr), venc(xte)
CHS = (50, 110, 170, ("on", 8))
if SET == "fsdd":
    z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; train_c = spk != spk.max(); test_c = spk == spk.max()
else:
    WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]; files, sy, spk = [], [], []
    for wi, w in enumerate(WORDS):
        for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); sy.append(wi); spk.append(int(f.split("_")[0], 16))
    sy = np.array(sy); grp = np.array(spk) % 5; X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)
    S = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(X), 500)]); train_c = grp >= 1; test_c = grp == 0
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); sfs = [SoundFeatures(32, c, 3, 3, 1, 1, 4, 4).fit(pic[train_c][:12000]) for c in CHS]; A = np.concatenate([f.encode(pic) for f in sfs], 1); tr_i, te_i = np.where(train_c)[0], np.where(test_c)[0]


def kmeans(X, k, seed, iters=25, restarts=RESTARTS):
    X = X.astype(np.float32); best = (-1e18, None); g = np.random.RandomState(seed)
    for _ in range(restarts):
        c = [X[g.randint(len(X))]]
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


R = {}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); heard = A[np.array([r.choice(tr_i[sy[tr_i] == d]) for d in ytr])]; joint = np.concatenate([vtr, heard], 1)
    tp = np.array([r.choice(te_i[sy[te_i] == d]) for d in yte]); jte = np.concatenate([vte, A[tp]], 1)
    a = kmeans(joint, K, seed); nm = np.zeros(K, np.int64)
    for j in range(K):
        mem = np.where(a == j)[0]; nm[j] = np.bincount(ytr[r.choice(mem, min(5, len(mem)), replace=False)], minlength=10).argmax() if len(mem) else 0
    names = nm[a]; R.setdefault("round 0: group names right", []).append(float((names == ytr).mean()))
    for rd in range(1, ROUNDS + 1):
        m = cross_modal.fit(joint, names, seed); names = cross_modal.clean_names(m, joint, names, KN=8, B=256, ear_vote=0)                  # the joint table re-names every pair with both senses, pooled over its neighbours
        R.setdefault("round %d: names right" % rd, []).append(float((names == ytr).mean()))
    mp = cross_modal.fit(vtr, names, seed); mj = cross_modal.fit(joint, names, seed)
    R.setdefault("picture learner on the final names (picture only test)", []).append(float((mp.predict(vte) == yte).mean())); R.setdefault("joint learner on the final names (both senses test)", []).append(float((mj.predict(jte) == yte).mean()))
    R.setdefault("reference: picture learner, all true labels", []).append(float((cross_modal.fit(vtr, ytr, seed).predict(vte) == yte).mean())); R.setdefault("reference: joint learner, all true labels", []).append(float((cross_modal.fit(joint, ytr, seed).predict(jte) == yte).mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
print("set", SET, "(10 labels in total, groups formed with no labels)")
for k, v in R.items(): print("%-64s %.4f" % (k, np.mean(v)), flush=True)
