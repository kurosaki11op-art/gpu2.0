"""SPARK core v0 — bit-exact integer reference ("golden") model.

The RTL in hw/rtl/spark_core.v must reproduce this model exactly: same
predictions, same path decisions and same event counts for every token.

Network (small demo size; real weights will come from the L export):
  byte -> embedding (D int4) -> layer 0 (H spiking neurons)
       -> layer 1 (H spiking neurons) -> main head (V logits)
  optional exit head (V logits) on layer-0 spikes, optional recall table.

Stages (each is "events x weight columns accumulated into acc"):
  stage 0: emb    (D) -> acc0 (H)  then membrane/spike pass -> s0
  stage 1: s0     (H) -> acc1 (H)  then membrane/spike pass -> s1
  stage 2: s0     (H) -> acc2 (V)  exit head, argmax + margin
  stage 3: s1     (H) -> acc3 (V)  main head, argmax
"""
import argparse
import json
import os

import numpy as np

P = 16                 # lanes (weights processed per cycle)
D, H, V = 64, 128, 256
T_BITS = 10            # recall table: 1024 entries


class Cfg:
    def __init__(self, **kw):
        self.sparse = 1      # 1: only non-zero events; 0: dense (every input)
        self.delta = 0       # 1: change-only events, persistent accumulators
        self.exit_en = 0     # 1: early-exit head after layer 0
        self.exit_th = 64    # margin threshold for early exit
        self.recall = 0      # 1: hippocampus-style recall table
        self.conf_th = 1     # recall confidence needed for bypass (0..3)
        self.cap = 0         # max non-zero events per stage per token (0 = off)
        self.adapt = 0       # 1: adaptive controller (per-stage change-only vs full
                             #    recompute, and adaptive early-exit probing)
        self.a = 230         # membrane decay, Q8 (230/256 ~ 0.9)
        self.acc_sh = 2      # accumulator -> membrane shift
        self.s_sh = 4        # membrane -> spike shift
        for k, v in kw.items():
            setattr(self, k, v)

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items()}


def sat16(x):
    return max(-32768, min(32767, x))


def spike(h, s_sh):
    mag = min(abs(h) >> s_sh, 7)
    s = mag if h >= 0 else -mag
    return s, h - s * (1 << s_sh)


def rhash(x):
    return (x ^ (x >> 10) ^ (x >> 20)) & ((1 << T_BITS) - 1)


class Weights:
    def __init__(self, seed=1):
        rng = np.random.default_rng(seed)

        def sparse_int4(shape, density):
            w = rng.integers(-7, 8, size=shape)
            w[rng.random(shape) > density] = 0
            return w.astype(np.int64)

        # emb[b] has 8 non-zero entries out of D
        self.emb = np.zeros((V, D), dtype=np.int64)
        for b in range(V):
            idx = rng.choice(D, size=8, replace=False)
            self.emb[b, idx] = rng.choice([-7, -5, -3, 3, 5, 7], size=8)
        self.w = [
            sparse_int4((H, D), 0.5),   # stage 0: [nout][nin]
            sparse_int4((H, H), 0.5),   # stage 1
            sparse_int4((V, H), 0.5),   # stage 2 (exit head)
            sparse_int4((V, H), 0.5),   # stage 3 (main head)
        ]

    def export_hex(self, outdir):
        os.makedirs(outdir, exist_ok=True)

        def lanes_hex(vals):
            word = 0
            for l, v in enumerate(vals):
                word |= (int(v) & 0xF) << (4 * l)
            return f"{word:0{P}x}"  # P lanes x 4 bits = P hex digits

        with open(os.path.join(outdir, "emb.hex"), "w") as f:
            for b in range(V):
                for c in range(D // P):
                    f.write(lanes_hex(self.emb[b, c * P:(c + 1) * P]) + "\n")
        for k, w in enumerate(self.w):
            nout, nin = w.shape
            with open(os.path.join(outdir, f"w{k}.hex"), "w") as f:
                for j in range(nin):           # column-major: one event = one column
                    for c in range(nout // P):
                        f.write(lanes_hex(w[c * P:(c + 1) * P, j]) + "\n")


class Golden:
    def __init__(self, wts, cfg):
        self.w, self.c = wts, cfg
        self.acc = [np.zeros(H, np.int64), np.zeros(H, np.int64),
                    np.zeros(V, np.int64), np.zeros(V, np.int64)]
        self.sent = [np.zeros(D, np.int64), np.zeros(H, np.int64),
                     np.zeros(H, np.int64), np.zeros(H, np.int64)]
        self.h = [np.zeros(H, np.int64), np.zeros(H, np.int64)]
        self.s = [np.zeros(H, np.int64), np.zeros(H, np.int64)]
        self.table = {}        # idx -> [valid, tag, value, conf]
        self.ctx_prev = 0
        self.tok = 0           # token index
        self.score = 8         # adaptive early-exit score (0..15)

    def _events(self, k, src):
        """Accumulate one stage. Returns (non-zero events, processed events)."""
        c, acc, sent, W = self.c, self.acc[k], self.sent[k], self.w.w[k]
        if c.adapt:
            # Adaptive controller: invariant acc == W @ sent. Pick the cheaper of
            # change-only events and a full recompute from the current input.
            n_nz = int(np.count_nonzero(src))
            n_dl = int(np.count_nonzero(src != sent))
            use_delta = n_dl <= n_nz
            if not use_delta:
                acc[:] = 0
                newsent = np.zeros_like(sent)
            nz = proc = 0
            for j in range(len(src)):
                v = int(src[j] - sent[j]) if use_delta else int(src[j])
                if v == 0 or (c.cap and nz >= c.cap):
                    continue
                nz += 1
                proc += 1
                acc += W[:, j] * v
                if use_delta:
                    sent[j] = src[j]
                else:
                    newsent[j] = src[j]
            if not use_delta:
                sent[:] = newsent
            self.delta_choices += int(use_delta)
            return nz, proc
        if not c.delta:
            acc[:] = 0
        nz = proc = 0
        for j in range(len(src)):
            v = int(src[j] - sent[j]) if c.delta else int(src[j])
            if c.sparse:
                if v == 0 or (c.cap and nz >= c.cap):
                    continue
            if v != 0:
                nz += 1
            proc += 1
            acc += W[:, j] * v
            if c.delta:
                sent[j] = src[j]
        return nz, proc

    def _membrane(self, layer, k):
        c = self.c
        for i in range(H):
            hv = sat16(((int(self.h[layer][i]) * c.a) >> 8)
                       + (int(self.acc[k][i]) >> c.acc_sh))
            s, hv = spike(hv, c.s_sh)
            self.h[layer][i], self.s[layer][i] = hv, s

    def _argmax(self, k):
        t1, t2, idx = -(1 << 30), -(1 << 30), 0
        for i, x in enumerate(self.acc[k]):
            x = int(x)
            if x > t1:
                t2, t1, idx = t1, x, i
            elif x > t2:
                t2 = x
        return idx, t1 - t2

    def step(self, b):
        c = self.c
        out = {"ev": [0, 0, 0, 0], "proc": [0, 0, 0, 0]}
        tok = self.tok
        self.tok += 1
        self.delta_choices = 0
        ctx = ((self.ctx_prev << 8) | b) & 0xFFFFFFFF
        if c.recall:
            iu = rhash(self.ctx_prev)
            e = self.table.get(iu, [0, 0, 0, 0])
            if e[0] and e[1] == self.ctx_prev:
                e = [1, e[1], e[2], min(e[3] + 1, 3)] if e[2] == b else [1, e[1], b, 0]
            else:
                e = [1, self.ctx_prev, b, 0]
            self.table[iu] = e
            self.ctx_prev = ctx
            e = self.table.get(rhash(ctx), [0, 0, 0, 0])
            if e[0] and e[1] == ctx and e[3] >= c.conf_th:
                out.update(pred=e[2], path=2)
                return out
        self.ctx_prev = ctx

        def stage(k, src):
            out["ev"][k], out["proc"][k] = self._events(k, src)

        stage(0, self.w.emb[b])
        self._membrane(0, 0)
        try_exit = c.exit_en and ((not c.adapt) or self.score >= 4 or (tok & 15) == 0)
        if try_exit:
            stage(2, self.s[0])
            idx, margin = self._argmax(2)
            if margin >= c.exit_th:
                self.score = min(self.score + 2, 15)
                out.update(pred=idx, path=1)
                return out
            self.score = max(self.score - 1, 0)
        stage(1, self.s[0])
        self._membrane(1, 1)
        stage(3, self.s[1])
        idx, _ = self._argmax(3)
        out.update(pred=idx, path=0)
        return out


def stim_text():
    snippet = (
        "def add(a, b):\n    return a + b\n\n"
        "class Point:\n    def __init__(self, x, y):\n        self.x = x\n        self.y = y\n\n"
        "for i in range(10):\n    print(add(i, i))\n"
    )
    other = "x = [i * i for i in range(20) if i % 3 == 0]\nprint(sum(x))\n"
    return (snippet + other + snippet + snippet).encode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="hw/build")
    ap.add_argument("--cfg", default="{}", help="JSON config overrides")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    cfg = Cfg(**json.loads(a.cfg))
    wts = Weights()
    data = stim_text()
    if a.export:
        wts.export_hex(a.out)
        with open(os.path.join(a.out, "stim.hex"), "w") as f:
            f.write("\n".join(f"{b:02x}" for b in data) + "\n")
        with open(os.path.join(a.out, "nbytes.txt"), "w") as f:
            f.write(str(len(data)))
    g = Golden(wts, cfg)
    with open(os.path.join(a.out, "golden.txt"), "w") as f:
        for b in data:
            o = g.step(b)
            f.write(f"{o['pred']} {o['path']} {' '.join(map(str, o['ev']))} "
                    f"{' '.join(map(str, o['proc']))}\n")


if __name__ == "__main__":
    main()
