#!/usr/bin/env python3
"""Drive SPARK Cortex on the Tang Nano 20K (cortex_board_top.v) through 5 learning stages, or emulate it.

The PC turns images into sensory codes (hw/brain/feature_layer.py) and sends them; the board learns, dreams, sleeps
and answers. The schedule is the month-2 rule (hw/brain/cortex_int.py): each real example once (count + practise),
one daydream of its class, dreams of old classes interleaved through the day, and a night of up to 2 passes that
ends after a block of 256 dreams with more than 2 surprises. The board reports every surprise, so the PC can end
the night exactly as the chip model does.

  python cortex_host.py --dry-run                        # emulator (needs numba), checks itself against the model
  python cortex_host.py --port COM5 --per-class 300      # real board, small quick run
  python cortex_host.py --port COM5                      # real board, full digits run (about an hour at 115200 baud)

Data: MNIST is downloaded to --data (default ./cortex_data) on first use. Put it on D: if C: is short of space,
e.g. --data D:\\cortex_data."""
import argparse, os, sys, time, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from feature_layer import Features  # noqa

SEED_LANES = [((0x9E3779B9 * (i + 1)) & 0xFFFFFFFF) or 1 for i in range(32)]     # same seeds as CortexInt(seed=1)
RULE = dict(ndream=6000, night=2, daydream=1, night_stop=2, top=1023, margin=8, cmax=15)


class Board:
    """rows given to learn/predict are sensory codes (bool, 4,608) or, with onchip=True, raw 28x28 images (uint8, 784)
    that the chip encodes itself (cortex_encoder.v; load the detectors first with detectors())"""
    def __init__(self, port, baud, onchip=False):
        import serial
        self.s = serial.Serial(port, baud, timeout=5); self.onchip = onchip

    def _x(self, out, n):
        self.s.write(bytes(out)); r = self.s.read(n)
        if len(r) != n:
            raise RuntimeError(f"board did not answer (sent {out[:3]}..., got {r!r})")
        return r

    def ping(self): return self._x([0xE0], 1) == b"\x5a"
    def seed(self, lanes): return self._x([0x53] + [b for v in lanes for b in int(v).to_bytes(4, "little")], 1)
    def clear(self): return self._x([0x43], 1)
    def known(self, c): return self._x([0x4B, c], 1)

    @staticmethod
    def _lst(a): return [len(a) & 255, len(a) >> 8] + [x for v in a for x in (int(v) & 255, int(v) >> 8)]

    def detectors(self, fes):
        words = [sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)]
        return self._x([0x54] + [b for w in words for b in w.to_bytes(4, "little")], 1)

    def learn(self, c, row):
        if self.onchip:
            return self._x([0x49, c] + [int(v) for v in row], 1)[0]
        return self._x([0x4C, c] + self._lst(np.nonzero(row)[0]), 1)[0]

    def predict(self, row):
        if self.onchip:
            return self._x([0x49, 0xFF] + [int(v) for v in row], 1)[0]
        return self._x([0x50] + self._lst(np.nonzero(row)[0]), 1)[0]

    def dream(self, c):
        r = self._x([0x44, c], 3); return r[0] | (r[1] << 8), r[2]

    def export(self, nb=4608):
        """read everything the chip knows: table, dream counts, example counts, known classes"""
        W = np.zeros((10, nb), np.int8); on = np.zeros((10, nb), np.uint16)
        for b in range(nb):
            r = self._x([0x52, b & 255, b >> 8], 20); w = int.from_bytes(r[:7], "little"); cw = int.from_bytes(r[7:], "little")
            for c in range(10):
                f = (w >> (5 * c)) & 31; W[c, b] = f - 32 if f >= 16 else f; on[c, b] = (cw >> (10 * c)) & 1023
        r = self._x([0x4E], 15); nv = int.from_bytes(r[:13], "little"); kv = int.from_bytes(r[13:], "little")
        n = np.array([(nv >> (10 * c)) & 1023 for c in range(10)], np.int32); kn = np.array([(kv >> c) & 1 for c in range(10)], bool)
        return {"W": W, "on": on, "n": n, "known": kn}

    def load(self, mem):
        """write a memory (e.g. a merge of two chips) into the chip"""
        for b in range(mem["W"].shape[1]):
            w = sum((int(mem["W"][c, b]) & 31) << (5 * c) for c in range(10)); cw = sum(int(mem["on"][c, b]) << (10 * c) for c in range(10))
            self._x([0x57, b & 255, b >> 8] + list(w.to_bytes(7, "little") + cw.to_bytes(13, "little")), 1)
        nv = sum(int(mem["n"][c]) << (10 * c) for c in range(10)); kv = sum(1 << c for c in range(10) if mem["known"][c])
        self._x([0x4D] + list(nv.to_bytes(13, "little") + kv.to_bytes(2, "little")), 1)


class Emu:
    """the board, emulated with the integer chip model's primitives (bit-exact with the RTL)"""
    def __init__(self, nb):
        from cortex_int import _count, _practise, _dream
        self.f = (_count, _practise, _dream)
        self.W = np.zeros((10, nb), np.int8); self.on = np.zeros((10, nb), np.uint16); self.n = np.zeros(10, np.int32)
        self.kn = np.zeros(10, np.bool_); self.rng = np.zeros(32, np.uint32); self.buf = np.zeros(nb, np.int32)

    def ping(self): return True
    def seed(self, lanes): self.rng[:] = lanes
    def clear(self): self.W[:] = 0; self.on[:] = 0; self.n[:] = 0; self.kn[:] = False
    def known(self, c): self.kn[c] = True

    def learn(self, c, row):
        a = np.nonzero(row)[0].astype(np.int32); self.f[0](self.on, self.n, a, len(a), c, RULE["top"])
        return self.f[1](self.W, a, len(a), c, self.kn, RULE["margin"], RULE["cmax"])

    def dream(self, c):
        k = self.f[2](self.on, self.n, c, self.rng, self.buf)
        return k, self.f[1](self.W, self.buf, k, c, self.kn, RULE["margin"], RULE["cmax"])

    def export(self, nb=None):
        return {"W": self.W.copy(), "on": self.on.copy(), "n": self.n.copy(), "known": self.kn.copy()}

    def load(self, mem):
        self.W[:] = mem["W"]; self.on[:] = mem["on"]; self.n[:] = mem["n"]; self.kn[:] = mem["known"]

    def predict(self, row):
        a = np.nonzero(row)[0]
        s = self.W[:, a].astype(np.int64).sum(1); s[~self.kn] = -(1 << 40); return int(s.argmax())


def merge(a, b, top=1023):
    """knowledge transfer: add the tables (saturating) and the dream counts (synaptic scaling when full)"""
    m = {"W": np.clip(a["W"].astype(np.int16) + b["W"], -15, 15).astype(np.int8), "on": (a["on"].astype(np.int32) + b["on"]),
         "n": a["n"].astype(np.int32) + b["n"], "known": a["known"] | b["known"]}
    for c in range(10):
        while m["n"][c] >= top:
            m["on"][c] >>= 1; m["n"][c] >>= 1
    m["on"] = m["on"].astype(np.uint16)
    return m


def night(dev, known):
    """one self-regulated night over all known classes"""
    kn = sorted(known); blockw = run = 0
    for _ in range(RULE["night"]):
        for j in range(RULE["ndream"] * len(kn)):
            blockw += dev.dream(kn[j % len(kn)])[1]; run += 1
            if run % 256 == 0:
                if blockw > RULE["night_stop"]:
                    return run
                blockw = 0
    return run


def run_stage(dev, code, y, known):
    """one stage, the same order of operations as cortex_int._stage"""
    new = sorted(set(y.tolist())); old = [c for c in sorted(known) if c not in new]
    for c in new:
        dev.known(c); known.add(c)
    total, done, rr = RULE["ndream"] * len(old), 0, 0
    for i in range(len(y)):
        dev.learn(int(y[i]), code[i])
        for _ in range(RULE["daydream"]):
            dev.dream(int(y[i]))
        due = (total * (i + 1)) // len(y)
        while done < due:
            dev.dream(old[rr % len(old)]); rr += 1; done += 1
    night = 0
    if old:
        kn = sorted(known); blockw = 0
        for _ in range(RULE["night"]):
            stop = False
            for j in range(RULE["ndream"] * len(kn)):
                blockw += dev.dream(kn[j % len(kn)])[1]; night += 1
                if night % 256 == 0:
                    if blockw > RULE["night_stop"]:
                        stop = True; break
                    blockw = 0
            if stop:
                break
    return night


def mnist(data):
    os.makedirs(data, exist_ok=True); f = os.path.join(data, "mnist.npz")
    if not os.path.exists(f):
        print("downloading MNIST to", f)
        urllib.request.urlretrieve("https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz", f)
    z = np.load(f)
    return z["x_train"].reshape(-1, 784), z["y_train"].astype(int), z["x_test"].reshape(-1, 784), z["y_test"].astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--per-class", type=int, default=0, help="examples per class per stage (0 = all)")
    ap.add_argument("--test", type=int, default=1000, help="test images scored after each stage")
    ap.add_argument("--onchip-encode", action="store_true", help="send raw images; the chip encodes them (board only)")
    a = ap.parse_args()
    xtr, ytr, xte, yte = mnist(a.data)
    stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
    print("learning feature detectors (no labels, images of the first stage only)...")
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, stages[0])][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    r = np.random.RandomState(0); tst = r.choice(len(yte), a.test, replace=False); cte = enc(xte[tst]); yt = yte[tst]
    onchip = a.onchip_encode and not a.dry_run
    dev = Emu(cte.shape[1]) if a.dry_run else Board(a.port, a.baud, onchip)
    if onchip:
        dev.detectors(fes); enc = lambda x: x; cte = xte[tst]                # the chip senses for itself
    if not dev.ping():
        sys.exit("no ping reply: check the port and that cortex_board_top is loaded")
    dev.seed(SEED_LANES); dev.clear(); known = set(); t0 = time.time()
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]
        if a.per_class:
            sel = np.concatenate([np.where(ytr == c)[0][:a.per_class] for c in s])
        sel = sel[np.random.RandomState(i).permutation(len(sel))]
        night = run_stage(dev, enc(xtr[sel]), ytr[sel], known)
        seen = np.isin(yt, sorted(known))
        acc = np.mean([dev.predict(cte[j]) == yt[j] for j in np.where(seen)[0]])
        print(f"stage {i + 1} (classes {s}): accuracy on all classes so far {acc:.3f}  night dreams {night}  "
              f"[{time.time() - t0:.0f}s]", flush=True)
    if a.dry_run:                                                           # self-check against the chip model
        from cortex_int import CortexInt
        ref = CortexInt(cte.shape[1], night=2, daydream=1, night_stop=2, seed=1)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]
            if a.per_class:
                sel = np.concatenate([np.where(ytr == c)[0][:a.per_class] for c in s])
            sel = sel[np.random.RandomState(i).permutation(len(sel))]; ref.stage(enc(xtr[sel]), ytr[sel])
        same = np.array_equal(ref.W, dev.W) and np.array_equal(ref.on, dev.on) and np.array_equal(ref.n, dev.n)
        print("emulator matches the integer chip model exactly:", same)


if __name__ == "__main__":
    main()
