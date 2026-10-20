"""Novelty from inside, with two senses (20 Oct 2026) SIMULATED. The chip knows digits 0-7 (picture + sound pairs, learned in 4 stages with dreams). An UNLABELLED stream of pairs follows (1,000 per digit: 20 % belong to digits 8 and 9 that it has never met, with sounds of words it does not know).
  1. novelty: a pair is flagged when the table's top score on its joint code falls below the 10th percentile of the top scores of known pairs (picture bits and sound bits can also be judged separately: 'either' / 'both' unfamiliar)
  2. groups: the flagged pairs form KG groups by competitive learning (k-means by overlap)
  3. names: each group is named by ONE label (the majority of 5 labelled members); a group named with a known digit merges into it (a false alarm), a group named 8 or 9 becomes (part of) a new class
  4. learning: the flagged pairs are learned under the group names (sleep-cleaned: neighbour pooling) as one stage with dreams of the old classes
Reported: novelty detection (AUROC, recall and precision of the flag), accuracy on all 10 digits and on the new digits alone (joint test with both senses; picture alone), old-digit accuracy before and after, against an oracle (true labels for the same stream) and against the picture-only version.
usage: DATA_DIR SUBSET_DIR (env SET = fsdd | sc, SEEDS, KG)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int, detector_learn, cross_modal
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
D, ROOT = sys.argv[1], sys.argv[2]; SET = os.environ.get("SET", "fsdd"); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = int(os.environ.get("SEEDS", 3)); KG = int(os.environ.get("KG", 6))
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
NP = vtr.shape[1]


def kmeans(X, k, seed, iters=25, restarts=3):
    X = X.astype(np.float32); best = (-1e18, None); g = np.random.RandomState(seed)
    for _ in range(restarts):
        c = [X[g.randint(len(X))]]
        for _k in range(1, k):
            d = np.min([((X - ci) ** 2).sum(1) for ci in c], 0); c.append(X[g.choice(len(X), p=d / (d.sum() + 1e-9))])
        c = np.stack(c)
        for _i in range(iters):
            sc = X @ c.T - 0.5 * (c * c).sum(1)[None, :]; a = sc.argmax(1)
            for j in range(k):
                if (a == j).any(): c[j] = X[a == j].mean(0)
        sc = X @ c.T - 0.5 * (c * c).sum(1)[None, :]; tot = float(sc.max(1).sum())
        if tot > best[0]: best = (tot, sc.argmax(1))
    return best[1]


def auroc(score_pos, score_neg):
    s = np.concatenate([score_pos, score_neg]); r = s.argsort().argsort() + 1; n1, n0 = len(score_pos), len(score_neg); return float((r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def build(table_labels, codes_by_stage):
    m = cross_modal.new_table(codes_by_stage[0][0].shape[1])
    for code, lab in codes_by_stage: m.stage(code, lab)
    return m


R = {}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); heard_all = A[np.array([r.choice(tr_i[sy[tr_i] == d]) for d in ytr])]; joint = np.concatenate([vtr, heard_all], 1)
    tp = np.array([r.choice(te_i[sy[te_i] == d]) for d in yte]); jte = np.concatenate([vte, A[tp]], 1); pte_only = vte
    known_pool, stream = [], []
    for c in range(10):
        ids = np.where(ytr == c)[0]; ids = ids[r.permutation(len(ids))]; (known_pool if c < 8 else []).extend(ids[:1000].tolist()); stream.extend(ids[1000:2000].tolist() if c < 8 else ids[:1000].tolist())
    known_pool = np.array(known_pool); stream = np.array(stream); stream = stream[r.permutation(len(stream))]; novel_true = ytr[stream] >= 8
    base_stages = [(joint[known_pool[np.isin(ytr[known_pool], s)]], ytr[known_pool][np.isin(ytr[known_pool], s)]) for s in STAGES[:4]]; base = build(None, base_stages)
    jstream = joint[stream]; ystream = ytr[stream]
    Sbase = base.S.astype(np.int32); sc_all = jstream.astype(np.int32) @ Sbase.T; sc_all[:, ~base.known] = -(1 << 30); top = sc_all.max(1)
    sc_known = joint[known_pool[:2000]].astype(np.int32) @ Sbase.T; sc_known[:, ~base.known] = -(1 << 30); top_known = sc_known.max(1); thr = np.percentile(top_known, 10)
    srt = np.sort(sc_all, 1); mg = srt[:, -1] - srt[:, -2]
    R.setdefault("novelty AUROC, top score of the joint code", []).append(auroc(-top[novel_true], -top[~novel_true])); R.setdefault("novelty AUROC, margin", []).append(auroc(-mg[novel_true], -mg[~novel_true]))
    pic_top = (jstream[:, :NP].astype(np.int32) @ Sbase[:, :NP].T); pic_top[:, ~base.known] = -(1 << 30); snd_top = (jstream[:, NP:].astype(np.int32) @ Sbase[:, NP:].T); snd_top[:, ~base.known] = -(1 << 30)
    R.setdefault("novelty AUROC, picture bits only", []).append(auroc(-pic_top.max(1)[novel_true], -pic_top.max(1)[~novel_true])); R.setdefault("novelty AUROC, sound bits only", []).append(auroc(-snd_top.max(1)[novel_true], -snd_top.max(1)[~novel_true]))
    flag = top < thr; R.setdefault("flag recall (new pairs flagged)", []).append(float(flag[novel_true].mean())); R.setdefault("flag precision (flagged that are new)", []).append(float(novel_true[flag].mean()) if flag.any() else 0.0); R.setdefault("flagged pairs", []).append(float(flag.sum()))
    fi = np.where(flag)[0]; a = kmeans(jstream[fi], min(KG, max(2, len(fi) // 20)), seed); nm = np.zeros(a.max() + 1, np.int64)
    for j in range(a.max() + 1):
        mem = np.where(a == j)[0]; nm[j] = np.bincount(ystream[fi][r.choice(mem, min(5, len(mem)), replace=False)], minlength=10).argmax() if len(mem) else 0
    names = nm[a]; R.setdefault("flagged pairs: group names right", []).append(float((names == ystream[fi]).mean()))
    m1 = cross_modal.fit(joint[stream[fi]], names, seed)                                      # names cleaned in sleep: pooled over neighbours, one round with the table learned on the names
    cleaned = cross_modal.clean_names(m1, joint[stream[fi]], names, KN=8, B=256, ear_vote=200); R.setdefault("flagged pairs: names right after sleep cleaning", []).append(float((cleaned == ystream[fi]).mean()))

    def run(label_codes, label_names, tag):
        m = build(None, base_stages)
        old_before = float((base.predict(jte[yte < 8]) == yte[yte < 8]).mean()) if tag == "ours" else None
        m.stage(label_codes, label_names)
        p = m.predict(jte); R.setdefault(tag + " | all 10 digits (both senses at test)", []).append(float((p == yte).mean())); R.setdefault(tag + " | new digits 8, 9 only", []).append(float((p[yte >= 8] == yte[yte >= 8]).mean())); R.setdefault(tag + " | old digits 0-7 after", []).append(float((p[yte < 8] == yte[yte < 8]).mean()))
        if old_before is not None: R.setdefault("old digits 0-7 before the new classes", []).append(old_before)
    run(joint[stream[fi]], cleaned, "ours (flag + groups + 30-ish names + sleep)")
    run(jstream, ystream, "oracle (true labels for the whole stream)")
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
print("set", SET)
for k, v in R.items(): print("%-80s %.4f" % (k, np.mean(v)), flush=True)
