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
