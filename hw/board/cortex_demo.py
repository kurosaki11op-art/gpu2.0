#!/usr/bin/env python3
"""Live demo: draw with the mouse, teach SPARK Cortex, ask it, let it sleep, and check it still knows the old digits.

  python cortex_demo.py                          # emulator (bit-exact with the chip; numba optional)
  python cortex_demo.py --port COM5              # the real Tang Nano 20K running cortex_board_top
  python cortex_demo.py --preload 300 --classes 0-7 --data D:\\cortex_data

--preload teaches that many MNIST examples of each class in --classes first (same day/night rule as the chip
model), so the chip starts out knowing those digits. Then draw new examples or a new symbol (use a free class
number, e.g. 8 = "star"), press Teach a few times, press Sleep, and press "Test old digits" to show nothing was
forgotten. Standard library GUI (tkinter) + numpy only."""
import argparse, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from cortex_host import Board, Emu, SEED_LANES, RULE, mnist, run_stage  # noqa
from feature_layer import Features  # noqa

SIDE, PEN = 280, 11


def to_mnist(canvas_img):
    """280x280 drawing (0..1) -> 28x28 uint8 like MNIST: crop, fit the longer side to 20 px, centre by mass"""
    ys, xs = np.nonzero(canvas_img > 0.1)
    if len(ys) == 0:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = canvas_img[y0:y1, x0:x1]; h, w = crop.shape; s = max(h, w)
    sq = np.zeros((s, s)); sq[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = crop
    e = np.linspace(0, s, 21).astype(int); small = np.zeros((20, 20))
    for i in range(20):
        for j in range(20):
            small[i, j] = sq[e[i]:max(e[i + 1], e[i] + 1), e[j]:max(e[j + 1], e[j] + 1)].mean()
    out = np.zeros((28, 28)); out[4:24, 4:24] = small
    m = out.sum(); cy = int(round((out.sum(1) * np.arange(28)).sum() / m)); cx = int(round((out.sum(0) * np.arange(28)).sum() / m))
    out = np.roll(np.roll(out, 14 - cy, 0), 14 - cx, 1)
    return np.clip(out / max(out.max(), 1e-6) * 255, 0, 255).astype(np.uint8).reshape(784)


class Brain:
    def __init__(self, dev, enc, xte, yte):
        self.dev, self.enc, self.xte, self.yte, self.known = dev, enc, xte, yte, set()
        self.counts = {}

    def teach(self, c, img, replay=20):
        if c not in self.known:
            self.dev.known(c); self.known.add(c)
        u = self.dev.learn(c, self.enc(img[None])[0]); self.dev.dream(c)                          # learn + one daydream
        old = sorted(self.known - {c})
        for j in range(replay if old else 0):                                # a little replay of old classes
            self.dev.dream(old[j % len(old)])
        self.counts[c] = self.counts.get(c, 0) + 1
        return u

    def ask(self, img):
        return self.dev.predict(self.enc(img[None])[0])

    def sleep(self, max_dreams=3000):
        kn = sorted(self.known); blockw = run = 0
        for j in range(max_dreams):
            blockw += self.dev.dream(kn[j % len(kn)])[1]; run += 1
            if run % 256 == 0:
                if blockw > RULE["night_stop"]:
                    break
                blockw = 0
        return run

    def test_old(self, n=200):
        sel = np.where(np.isin(self.yte, sorted(self.known)))[0][:n]
        if len(sel) == 0:
            return None
        return float(np.mean([self.ask(self.xte[i]) == self.yte[i] for i in sel])), len(sel)


def main():
    import tkinter as tk
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--preload", type=int, default=200); ap.add_argument("--classes", default="0-7")
    a = ap.parse_args()
    xtr, ytr, xte, yte = mnist(a.data)
    print("learning feature detectors (no labels)...")
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
    dev = Board(a.port, a.baud) if a.port else Emu(4608)
    dev.seed(SEED_LANES); dev.clear()
    brain = Brain(dev, enc, xte, yte)
    lo, hi = (int(v) for v in a.classes.split("-"))
    if a.preload:
        print(f"pre-teaching digits {lo}-{hi}, {a.preload} each, in stages of two...")
        for s0 in range(lo, hi + 1, 2):
            s = [c for c in (s0, s0 + 1) if c <= hi]
            sel = np.concatenate([np.where(ytr == c)[0][:a.preload] for c in s]); sel = sel[np.random.RandomState(s0).permutation(len(sel))]
            run_stage(dev, enc(xtr[sel]), ytr[sel], brain.known)
        print("ready")

    root = tk.Tk(); root.title("SPARK Cortex - teach me")
    cv = tk.Canvas(root, width=SIDE, height=SIDE, bg="black"); cv.grid(row=0, column=0, rowspan=8)
    img = np.zeros((SIDE, SIDE)); last = [None]
    yy, xx = np.mgrid[0:SIDE, 0:SIDE]

    def paint(ev):
        if last[0]:
            n = int(max(abs(ev.x - last[0][0]), abs(ev.y - last[0][1])) // 3) + 1
            for t in np.linspace(0, 1, n):
                px = last[0][0] + t * (ev.x - last[0][0]); py = last[0][1] + t * (ev.y - last[0][1])
                img[(yy - py) ** 2 + (xx - px) ** 2 <= PEN ** 2] = 1.0
            cv.create_line(last[0][0], last[0][1], ev.x, ev.y, fill="white", width=2 * PEN, capstyle=tk.ROUND)
        last[0] = (ev.x, ev.y)
    cv.bind("<B1-Motion>", paint); cv.bind("<ButtonRelease-1>", lambda e: last.__setitem__(0, None))

    msg = tk.StringVar(value=f"Knows classes {sorted(brain.known)}. Draw, then Teach or Ask.")
    tk.Label(root, textvariable=msg, wraplength=260, justify="left").grid(row=0, column=1, columnspan=2)
    tk.Label(root, text="class 0-9:").grid(row=1, column=1); cls = tk.Entry(root, width=4); cls.insert(0, str(hi + 1 if hi < 9 else 0)); cls.grid(row=1, column=2)

    def clear():
        img[:] = 0; cv.delete("all")

    def teach():
        x = to_mnist(img)
        if x is None:
            return msg.set("Draw something first.")
        c = int(cls.get()); u = brain.teach(c, x); clear()
        msg.set(f"Learned an example of class {c} ({brain.counts[c]} so far){' - it surprised me' if u else ''}.")

    def ask():
        x = to_mnist(img)
        if x is None:
            return msg.set("Draw something first.")
        msg.set(f"I think this is class {brain.ask(x)}."); clear()

    def sleep():
        t = time.time(); n = brain.sleep(); msg.set(f"Slept: {n} dreams in {time.time() - t:.1f} s.")

    def test():
        r = brain.test_old()
        msg.set("Nothing learned yet." if r is None else f"Test on {r[1]} real digits of the known classes: {100 * r[0]:.1f}% correct.")

    for i, (t, f) in enumerate([("Teach", teach), ("What is it?", ask), ("Clear", clear), ("Sleep", sleep), ("Test old digits", test)]):
        tk.Button(root, text=t, command=f, width=16).grid(row=2 + i, column=1, columnspan=2)
    root.mainloop()


if __name__ == "__main__":
    main()
