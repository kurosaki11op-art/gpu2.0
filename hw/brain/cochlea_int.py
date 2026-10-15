"""Integer cochlea (bit-exact reference for an RTL resonator bank): the 28 resonators of cochlea.sound_picture_res
with every multiply replaced by its shift-add terms, on integers with FB fractional bits.

Per resonator and sample:  y[n] = g (x[n] - x[n-2]) + a1 y[n-1] - a2 y[n-2], where a1, a2 are sums of up to 4 signed
powers of two (cochlea.csd) and g a power of two; every term is an arithmetic shift of an integer (right shifts round
toward minus infinity). Each 1/28 s frame sums |y| >> FB. Noise floor (auditory adaptation, default on): per
resonator, the floor is the sum of its 4 quietest frames with the two low bits cleared (= 4 x their mean); it is
subtracted from every frame sum (floor at 1). The picture is then the same integer log as the float version.
Only shifts, adds, compares. SIMULATED."""
import numpy as np
import cochlea
try:
    import numba
    njit = numba.njit(cache=True)
except ImportError:                                                  # pragma: no cover
    njit = lambda f: f

FB = 8


def terms(v, n=4, lo=-14):
    """the signed power-of-two terms cochlea.csd sums: list of (sign, exponent)"""
    out, acc, r = [], 0.0, v
    for _ in range(n):
        if r == 0:
            break
        e = int(np.round(np.log2(abs(r)))); e = max(e, lo)
        s = int(np.sign(r)); out.append((s, e)); acc += s * 2.0 ** e; r = v - acc
    return out


def tables():
    """per resonator: 4 (sign, exp) slots for a1, 4 for a2 (sign 0 = unused), and the gain exponent"""
    A1 = np.zeros((cochlea.CH, 4, 2), np.int64); A2 = np.zeros((cochlea.CH, 4, 2), np.int64); G = np.zeros(cochlea.CH, np.int64)
    for k, f in enumerate(cochlea.CF):
        erb = 24.7 * (4.37 * f / 1000 + 1)
        r = np.exp(-np.pi * erb / cochlea.FS); th = 2 * np.pi * f / cochlea.FS
        for t, (s, e) in enumerate(terms(2 * r * np.cos(th))):
            A1[k, t] = (s, e)
        for t, (s, e) in enumerate(terms(r * r)):
            A2[k, t] = (s, e)
        G[k] = int(np.round(np.log2(cochlea.RES[k][2])))
        a1 = sum(s * 2.0 ** e for s, e in A1[k] if s); a2 = sum(s * 2.0 ** e for s, e in A2[k] if s)
        assert abs(a1 - cochlea.RES[k][0]) < 1e-12 and abs(a2 - cochlea.RES[k][1]) < 1e-12
    return A1, A2, G


@njit
def _sh(v, e):
    return (v << e) if e >= 0 else (v >> (-e))


@njit
def _bank(x, A1, A2, G, FR, fb):
    B, N = x.shape; C = A1.shape[0]; fl = N // FR
    out = np.zeros((B, C, FR), np.int64)
    for b in range(B):
        for k in range(C):
            y1 = 0; y2 = 0; x1 = 0; x2 = 0; acc = 0; fr = 0; cnt = 0
            for n in range(fl * FR):
                xn = np.int64(x[b, n])
                y = _sh(xn - x2, G[k] + fb)
                for t in range(4):
                    if A1[k, t, 0] != 0:
                        y += A1[k, t, 0] * _sh(y1, A1[k, t, 1])
                    if A2[k, t, 0] != 0:
                        y -= A2[k, t, 0] * _sh(y2, A2[k, t, 1])
                y2 = y1; y1 = y; x2 = x1; x1 = xn
                acc += (y if y >= 0 else -y) >> fb
                cnt += 1
                if cnt == fl:
                    out[b, k, fr] = acc; acc = 0; cnt = 0; fr += 1
    return out


A1, A2, G = tables()


def noise_floor(S):
    """S: (B, 28, 28) frame sums -> frame sums minus each resonator's floor (sum of its 4 quietest frames, low 2 bits
    cleared), at least 1"""
    S = np.asarray(S, np.int64); fl = np.sort(S, 2)[:, :, :4].sum(2, keepdims=True) & ~3
    return np.maximum(S - fl, 1)


def align_word(P, lead=4):
    """Word alignment (attention to the word's start): P (B, 784) pictures, row = resonator, column = frame. A frame's
    loudness is the sum of its 28 pixels; the word starts at the first frame reaching 3/4 of the loudest frame
    ((max * 3) >> 2); every row is shifted so that frame lands at column `lead`, vacated columns are 0."""
    P0 = np.asarray(P).reshape(len(P), 28, 28); loud = P0.astype(np.int64).sum(1)
    start = np.argmax(loud >= (loud.max(1, keepdims=True) * 3 >> 2), 1); out = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0:
            out[i, :, sh:] = P0[i, :, :28 - sh]
        else:
            out[i, :, :28 + sh] = P0[i, :, -sh:]
    return out.reshape(len(P), -1)


def sound_picture_int(x, floor=True, lead=None):
    """x: (B, 16000) int16 samples -> (B, 784) uint8 sound pictures (28 resonators x 28 frames); lead: word alignment
    (align_word) with the word's start at that frame, None = off"""
    S = _bank(np.asarray(x, np.int64), A1, A2, G, cochlea.FR, FB)
    v = noise_floor(S) if floor else np.maximum(S, 1)
    e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3)
    top = lg.reshape(len(x), -1).max(1)[:, None, None]
    P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(x), -1).astype(np.uint8)
    return P if lead is None else align_word(P, lead)
