"""Cochlea front end for SPARK Cortex: sound -> 28x28 "sound picture", the way the inner ear does it.

  * filter cascade   : like the travelling wave along the cochlea, 28 low-pass stages in a row, each passing a bit
                       less high pitch (7 kHz at the base down to 100 Hz at the apex). Stage k: y += (x - y) * a_k,
                       with a_k a sum of two powers of two, so each stage is two shifts and adds, no multiplier.
  * hair cells       : each channel = difference of neighbouring stages (a band), rectified (absolute value) and
                       summed over 28 time frames of ~36 ms.
  * loudness         : log by leading-zero count (priority encoder) plus 2 fraction bits.
  * gain control     : the loudest point of the clip is pinned to the top of the range (outer hair cells / AGC), so
                       quiet and loud speakers look alike.
Simulation note: the stages run as float first-order filters with exactly those shift-add coefficients
(scipy.signal.lfilter); an integer version differs only by rounding. Labels: SIMULATED."""
import os, wave
import numpy as np
from scipy.signal import lfilter

WORDS = ["yes", "no", "up", "down", "left", "right", "on", "off", "stop", "go"]
FS, N, CH, FR = 16000, 16000, 28, 28


def shift_add(a):
    """nearest value to a of the form 2^-i + 2^-j, 2^-i, or 1 - 2^-j (each is shifts and adds)"""
    cands = [2.0 ** -i + (2.0 ** -j if j else 0) for i in range(1, 14) for j in list(range(i + 1, 16)) + [None]]
    cands += [1 - 2.0 ** -j for j in range(2, 8)]
    return min(cands, key=lambda v: abs(np.log(v / a)))


CUTS = np.geomspace(7000, 100, CH + 1)
ALPHA = [shift_add(1 - np.exp(-2 * np.pi * f / FS)) for f in CUTS]


def read(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64)
    out = np.zeros(N); out[:min(N, len(x))] = x[:N]
    return out


def sound_picture(x):
    """x: (B, N) samples -> (B, 28*28) uint8, rows = frequency channels (high to low), cols = time"""
    stages, y = [], x
    for a in ALPHA:
        y = lfilter([a], [1, a - 1], y, axis=1); stages.append(y)
    fl = N // FR
    pic = np.stack([np.abs(stages[k] - stages[k + 1])[:, :fl * FR].reshape(len(x), FR, fl).sum(2) for k in range(CH)], 1)
    v = np.maximum(pic.astype(np.int64), 1)
    e = np.floor(np.log2(v)).astype(np.int64)                                # leading-zero count
    frac = (v >> np.maximum(e - 2, 0)) & 3
    lg = 4 * e + frac                                                        # ~ 4*log2, integers
    top = lg.reshape(len(x), -1).max(1)[:, None, None]
    img = np.clip(255 - (top - lg) * 8, 0, 255)                              # AGC: loudest point = 255, 8 per quarter-octave of level
    return img.reshape(len(x), -1).astype(np.uint8)


def load_speech(root, cache=None, fn=None):
    fn = fn or sound_picture
    if cache and os.path.exists(cache):
        z = np.load(cache); return z["xtr"], z["ytr"], z["xte"], z["yte"]
    test = set(open(os.path.join(root, "testing_list.txt")).read().split())
    xs, ys, te = [], [], []
    for c, w in enumerate(WORDS):
        for f in sorted(os.listdir(os.path.join(root, w))):
            xs.append(read(os.path.join(root, w, f))); ys.append(c); te.append(f"{w}/{f}" in test)
    X = np.stack(xs); y = np.array(ys); te = np.array(te)
    P = np.concatenate([fn(X[i:i + 1000]) for i in range(0, len(X), 1000)])
    out = P[~te], y[~te], P[te], y[te]
    if cache:
        np.savez_compressed(cache, xtr=out[0], ytr=out[1], xte=out[2], yte=out[3])
    return out


def log_mel(root, cache):
    """Standard baseline features (FFT + mel filters + log), for the neural-network comparison only."""
    if os.path.exists(cache):
        z = np.load(cache); return z["xtr"], z["ytr"], z["xte"], z["yte"]
    test = set(open(os.path.join(root, "testing_list.txt")).read().split())
    nfft, hop, nm = 512, 320, 40
    mel = lambda f: 2595 * np.log10(1 + f / 700)
    pts = 700 * (10 ** (np.linspace(mel(20), mel(8000), nm + 2) / 2595) - 1)
    bins = np.floor((nfft + 1) * pts / FS).astype(int)
    fb = np.zeros((nm, nfft // 2 + 1))
    for m in range(1, nm + 1):
        l, c, r = bins[m - 1], bins[m], bins[m + 1]
        fb[m - 1, l:c] = (np.arange(l, c) - l) / max(c - l, 1); fb[m - 1, c:r] = (r - np.arange(c, r)) / max(r - c, 1)
    feats, ys, te = [], [], []
    win = np.hanning(nfft)
    for c, w in enumerate(WORDS):
        for f in sorted(os.listdir(os.path.join(root, w))):
            x = read(os.path.join(root, w, f))
            fr = np.stack([x[i:i + nfft] * win for i in range(0, N - nfft + 1, hop)])
            feats.append(np.log(np.abs(np.fft.rfft(fr)) ** 2 @ fb.T + 1e-6).astype(np.float32).ravel())
            ys.append(c); te.append(f"{w}/{f}" in test)
    X = np.stack(feats); y = np.array(ys); te = np.array(te)
    X = (X - X[~te].mean(0)) / (X[~te].std(0) + 1e-6)
    np.savez_compressed(cache, xtr=X[~te], ytr=y[~te], xte=X[te], yte=y[te])
    return X[~te], y[~te], X[te], y[te]


# ---- v2: resonator bank (sharper, like the basilar membrane's tuned resonances) --------------------------------
def csd(v, terms=4, lo=-14):
    """v rounded to a sum of `terms` signed powers of two (shift-add constant)"""
    out, r = 0.0, v
    for _ in range(terms):
        if r == 0:
            break
        e = int(np.round(np.log2(abs(r)))); e = max(e, lo)
        t = np.sign(r) * 2.0 ** e; out += t; r = v - out
    return out


CF = np.geomspace(6000, 120, CH)                                           # centre frequencies, base -> apex


def _res(f):
    erb = 24.7 * (4.37 * f / 1000 + 1)
    r = np.exp(-np.pi * 1.0 * erb / FS); th = 2 * np.pi * f / FS
    a1, a2 = csd(2 * r * np.cos(th)), csd(r * r)
    # peak gain of (1 - z^-2) / (1 - a1 z^-1 + a2 z^-2) at f, normalised by a power of two
    z = np.exp(-1j * th); gpk = abs((1 - z ** 2) / (1 - a1 * z + a2 * z ** 2))
    return a1, a2, 2.0 ** -np.round(np.log2(gpk))


RES = [_res(f) for f in CF]


def sound_picture_res(x):
    fl = N // FR
    pic = []
    for a1, a2, g in RES:
        y = lfilter([g, 0, -g], [1, -a1, a2], x, axis=1)
        pic.append(np.abs(y)[:, :fl * FR].reshape(len(x), FR, fl).sum(2))
    v = np.maximum(np.stack(pic, 1).astype(np.int64), 1)
    e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3)
    top = lg.reshape(len(x), -1).max(1)[:, None, None]
    return np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(x), -1).astype(np.uint8)
