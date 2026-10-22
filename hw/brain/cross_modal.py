"""Cross-modal (two-sense) learning for the counting chip (20 Oct 2026). SIMULATED model of host-side sleep logic around the chip's own table; no multiplies, no backprop, nothing stored but a small buffer.
  heard_names(ear, heard_codes)         the ear (a chip table trained on labelled sound codes) names each heard clip: the name a seen picture is learned under (zero picture labels)
  clean_names(table, codes, names, ...) sleep: pictures wait in a buffer of B; the K buffered pictures that overlap each picture most (popcount of AND) pool their class scores with its own, optionally plus a vote for the name the ear gave; the pooled winner is the new name
  learn_picture(codes, names, ...)      learns the pictures under the (cleaned) names in one pass on a CortexSlow table, 1-2 cleaning rounds
  joint_code(picture_code, sound_code)  one table over both senses (concatenated bits)
Results (MNIST + FSDD, 3 seeds): ear right on 73.5 % of unfamiliar speakers; pictures learned from its names 89.7; after cleaning 93.9; true labels 97.4; both senses in one table 98.33. See docs/journal.md (20 Oct 2026 night)."""
import numpy as np
from cortex_slow import CortexSlow


def new_table(n_bits, seed=1, **kw):
    cfg = dict(ch=100, K=5, night_stop=2, daydream=1, margin=256, ndream=1500, night=1); cfg.update(kw)
    return CortexSlow(n_bits, seed=seed, **cfg)


def fit(codes, labels, seed=1, **kw):
    m = new_table(codes.shape[1], seed, **kw); o = np.random.RandomState(seed).permutation(len(labels)); m.stage(codes[o], labels[o]); return m


def heard_names(ear, heard_codes):
    return ear.predict(heard_codes)


def clean_names(table, codes, names, KN=8, B=256, ear_vote=200):
    """one cleaning pass over the buffered pictures; returns the pooled names"""
    S = table.S.astype(np.int64); out = names.copy()
    for j in range(0, len(codes), B):
        c = codes[j:j + B]; s = c.astype(np.int32) @ S.T; ov = c.astype(np.int32) @ c.T.astype(np.int32); np.fill_diagonal(ov, -1)
        nn = np.argsort(-ov, 1, kind='stable')[:, :KN]; z = np.where(table.known[None, :], s, 0); pooled = z + z[nn].sum(1)
        if ear_vote: pooled[np.arange(len(c)), names[j:j + B]] += ear_vote * (KN + 1)
        out[j:j + B] = np.where(table.known[None, :], pooled, -(1 << 50)).argmax(1)
    return out


def cue_index(margin, T):
    """confidence index of a sense: how many of the 7 ascending thresholds its score margin reaches (0..7 = exponent + 4); thresholds are the typical clean margin times 2^(k-0.5), k = -3..3, loaded by the host"""
    return (np.asarray(margin)[..., None] >= np.asarray(T)).sum(-1)


def cue_margin(scores, known, big):
    """top score minus runner-up among the known classes (one known class: saturated to big; none: 0)"""
    s = np.where(known[None, :], scores, -(1 << 40)).astype(np.int64); t = np.sort(s, 1)
    m = t[:, -1] - t[:, -2]; nk = int(known.sum())
    return np.full(len(s), big if nk == 1 else 0, np.int64) if nk <= 1 else m


def cue_combine(sa, sb, known, TA, TB, sw=20):
    """reliability-weighted cue combination of two senses' class scores (shifts only): returns (pred, index A, index B); first known class wins ties"""
    big = (1 << (sw + 1)) - 1
    ia, ib = cue_index(cue_margin(sa, known, big), TA), cue_index(cue_margin(sb, known, big), TB); i0 = np.minimum(ia, ib)
    comb = (sa.astype(np.int64) << (ia - i0)[:, None]) + (sb.astype(np.int64) << (ib - i0)[:, None]); comb = np.where(known[None, :], comb, -(1 << 50))
    return comb.argmax(1), ia, ib


def look_combine(sa, sb, known, th, sw=20):
    """second look: table A answers alone when its top-2 margin is at least th; otherwise A and B scores are added; first known class wins ties. returns (pred, look flags)"""
    big = (1 << (sw + 1)) - 1; look = cue_margin(sa, known, big) < th
    comb = sa.astype(np.int64) + np.where(look[:, None], sb.astype(np.int64), 0); comb = np.where(known[None, :], comb, -(1 << 50))
    return comb.argmax(1), look


def quantile_track(x, n, e0=9, k=7, emin=2, w=21):
    """streaming quantile estimate on the chip (shifts and adds only): tracks the value q below which a share n/16 of the stream lies. q starts at the first sample; for every further sample x: if x < q then q -= (16 - n) << e else q += n << e (stationary point: share(x < q) = n/16); the step shift e = max(emin, e0 - (count >> k)) shrinks as samples arrive. returns the list of q after each sample"""
    q = int(x[0]); out = [q]
    for t in range(1, len(x)):
        e = max(emin, e0 - (t >> k))
        q = q - ((16 - n) << e) if int(x[t]) < q else q + (n << e)
        q = min(max(q, 0), (1 << w) - 1); out.append(q)
    return out


def cue_thresholds(ref, w=21):
    """the 7 cue-weighting thresholds ref * 2^(k - 0.5), k = -3..3, from shifts and adds only: ref * 2^-0.5 ~ (ref * 181) >> 8 with 181 = 128 + 32 + 16 + 4 + 1; then shifted by k (rounded up when shifting right)"""
    r = int(ref); h = ((r << 7) + (r << 5) + (r << 4) + (r << 2) + r + 255) >> 8
    return [min(((h >> -k) + (1 if (h & ((1 << -k) - 1)) else 0)) if k < 0 else h << k, (1 << w) - 1) for k in range(-3, 4)]


def novelty_threshold(known_tops, n=2, w=20, e0=9, k=7, emin=2):
    """novelty flag threshold on the chip: the streaming quantile tracker (n/16 of known pairs fall below it) run over the top scores of pairs the chip knows; signed scores are mapped to ordered unsigned values by flipping the sign bit; returns the signed threshold. A pair is flagged when its top score is below it."""
    flip = 1 << (w - 1); q = quantile_track([int(v) + flip for v in known_tops], n, e0, k, emin, w)[-1]
    return q - flip


def kmeans_int(X, k, iters=8, restarts=3):
    """label-free grouping on the chip, integers only (the sleep-time buffer of unlabelled pairs, X = bool codes): binary prototypes by majority vote.
    score of a pair x for prototype j: 2 * overlap(x, p_j) - |p_j|  (the k-means distance with binary centroids: popcounts, shifts, compares; first prototype wins ties)
    init (farthest first): prototype 0 = the first pair of the restart; each further prototype = the pair whose best score against the prototypes so far is smallest (lowest index on ties)
    iteration: assign every pair; per prototype count the on-bits of its members (c) and the members (m); the new prototype has bit b when 2 * c[b] >= m (an empty prototype keeps its bits)
    restart r starts with pair (r * N) // restarts; the restart with the largest total score wins (first on ties). returns the assignment of every pair"""
    X = np.asarray(X, bool); N = len(X); Xi = X.astype(np.int32); best = (None, None)
    for r in range(restarts):
        first = (r * N) // restarts; P = np.zeros((k, X.shape[1]), bool); P[0] = X[first]; used = 1
        for j in range(1, k):
            sc = 2 * (Xi @ P[:j].T.astype(np.int32)) - P[:j].sum(1)[None, :]; far = int(np.argmin(sc.max(1))); P[j] = X[far]; used += 1
        for _ in range(iters):
            sc = 2 * (Xi @ P.T.astype(np.int32)) - P.sum(1)[None, :]; a = sc.argmax(1)
            for j in range(k):
                m = int((a == j).sum())
                if m: P[j] = 2 * Xi[a == j].sum(0) >= m
        sc = 2 * (Xi @ P.T.astype(np.int32)) - P.sum(1)[None, :]; a = sc.argmax(1); tot = int(sc.max(1).sum())
        if best[0] is None or tot > best[0]: best = (tot, a)
    return best[1]


def pool_names(scores, nb_ids, names, known, ear_vote=200):
    """host-side pooling, exactly what the chip leaves to the host: scores (n, classes) = the core's class scores per buffered picture (rd_scores after a PREDICT), nb_ids (n, K) = the K neighbour slots of every picture (cortex_neighbours),
    names = the ear's names; new name = argmax over the known classes of own score + sum of the neighbours' scores (+ ear_vote x (K+1) for the ear's own name). Integer adds and compares."""
    K = nb_ids.shape[1]; z = np.where(known[None, :], scores, 0).astype(np.int64); pooled = z + z[nb_ids].sum(1)
    if ear_vote: pooled[np.arange(len(z)), names] += ear_vote * (K + 1)
    return np.where(known[None, :], pooled, -(1 << 50)).argmax(1)


def learn_picture(codes, names, rounds=2, seed=1, **kw):
    """pictures learned under the ear's names, cleaned in sleep for `rounds` rounds; returns (table, final names)"""
    lab = names; m = fit(codes, lab, seed, **kw)
    for _ in range(rounds): lab = clean_names(m, codes, names); m = fit(codes, lab, seed, **kw)
    return m, lab


def joint_code(picture_code, sound_code):
    return np.concatenate([picture_code, sound_code], 1)
