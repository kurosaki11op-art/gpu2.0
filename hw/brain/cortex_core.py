"""SPARK Cortex core, software model (bit-exact reference for the RTL to come).

Brain principles only, no matrices, no multiplies, no backprop:
  * sparse binary spikes   : each input value becomes on/off bits (thermometer code, like receptor thresholds)
  * dendrite = memory      : a neuron watches a fixed random handful of input bits; that bit pattern is an
                             address into its own small memory (a lookup, not a weighted sum)
  * local learning         : seeing an example of class c increments one small saturating counter per neuron
                             in class c's column (Hebbian "fire together, wire together"); one pass, no gradients
  * columns vote           : class score = how many of its neurons recognise the pattern (count >= threshold)
  * forgetting threshold   : the threshold b ignores rare, noisy memories (like synaptic pruning)
Addresses use an H3 hash (XOR of fixed random constants), so the hardware is wires + XOR + RAM + counters."""
import gzip, os, numpy as np


def load(data_dir, name):
    if name == "mnist":
        z = np.load(os.path.join(data_dir, "mnist.npz"))
        return z["x_train"].reshape(-1, 784), z["y_train"], z["x_test"].reshape(-1, 784), z["y_test"]
    rd = lambda f, off: np.frombuffer(gzip.open(os.path.join(data_dir, f"{name}-{f}")).read(), np.uint8, offset=off)
    return (rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784), rd("train-labels-idx1-ubyte.gz", 8),
            rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 784), rd("t10k-labels-idx1-ubyte.gz", 8))


class Cortex:
    def __init__(self, n_in, n_cls, levels=(64, 128, 192), tuple_bits=16, addr_bits=10, copies=4, seed=0, cmax=255,
                 hashes=1, local=0, side=28):
        r = np.random.RandomState(seed)
        self.levels, self.C, self.T, self.cmax, self.k = np.array(levels, np.uint8), n_cls, addr_bits, cmax, hashes
        L = len(levels); nb = n_in * L
        if local:   # local receptive fields: a neuron samples bits near one spot, like a V1 cell
            per = nb // tuple_bits * copies
            cy, cx = r.randint(0, side, per), r.randint(0, side, per)
            dy, dx = r.randint(-local, local + 1, (per, tuple_bits)), r.randint(-local, local + 1, (per, tuple_bits))
            py, px = np.clip(cy[:, None] + dy, 0, side - 1), np.clip(cx[:, None] + dx, 0, side - 1)
            self.wires = (py * side + px) * L + r.randint(0, L, (per, tuple_bits))
        else:       # each copy is a different random wiring of the same input bits
            self.wires = np.concatenate([r.permutation(nb)[: nb // tuple_bits * tuple_bits].reshape(-1, tuple_bits)
                                         for _ in range(copies)])
        self.N = len(self.wires)
        self.h3 = r.randint(0, 1 << addr_bits, size=(hashes, self.N, tuple_bits)).astype(np.int32)
        self.mem = np.zeros((n_cls, self.N, 1 << addr_bits), np.uint8)

    def spikes(self, x):
        return x[:, :, None] > self.levels[None, None, :]

    def addr(self, x):
        b = self.spikes(x).reshape(len(x), -1)[:, self.wires]                # (B, N, tuple) on/off
        a = np.zeros((self.k,) + b.shape[:2], np.int32)
        for t in range(b.shape[2]):                                         # XOR-only hash (k of them: Bloom filter)
            a ^= np.where(b[None, :, :, t], self.h3[:, None, :, t], 0)
        return a                                                            # (k, B, N)

    def learn(self, x, y, bs=2000):
        for i in range(0, len(x), bs):
            a, yy = self.addr(x[i:i + bs]), y[i:i + bs]
            n = np.broadcast_to(np.arange(self.N), a.shape)
            cnt = np.zeros_like(self.mem, np.int32)
            np.add.at(cnt, (np.broadcast_to(yy[None, :, None], a.shape), n, a), 1)
            self.mem = np.minimum(self.mem.astype(np.int32) + cnt, self.cmax).astype(np.uint8)

    def learn_surprise(self, x, y, epochs=3, margin=None, bs=200, seed=0):
        """Learn only from surprise (predictive coding + a reward signal). Memory holds small signed counters.
        Per example: score each class by adding its neurons' counters. If the true class does not win by `margin`,
        +1 to the true class's active counters and -1 to the rival's active counters. Nothing else changes."""
        r = np.random.RandomState(seed)
        if self.mem.dtype != np.int8:
            self.mem = np.zeros(self.mem.shape, np.int8)
        margin = self.N // 8 if margin is None else margin
        ar = np.arange(self.N)
        for ep in range(epochs):
            o, wrote = r.permutation(len(x)), 0
            for i in range(0, len(x), bs):
                idx = o[i:i + bs]; a = self.addr(x[idx])[0]; yy = y[idx]
                sc = self.mem[:, ar[None, :], a].astype(np.int32).sum(2).T          # (B, C) additions only
                true = sc[np.arange(len(idx)), yy]
                sc[np.arange(len(idx)), yy] = -1 << 30
                rival = sc.argmax(1)
                sup = (true - sc[np.arange(len(idx)), rival]) <= margin            # surprised?
                if not sup.any():
                    continue
                a, yy, rv = a[sup], yy[sup], rival[sup]; wrote += sup.sum()
                d = np.zeros(self.mem.shape, np.int32); n = np.broadcast_to(ar, a.shape)
                np.add.at(d, (np.broadcast_to(yy[:, None], a.shape), n, a), 1)
                np.add.at(d, (np.broadcast_to(rv[:, None], a.shape), n, a), -1)
                self.mem = np.clip(self.mem + d, -self.cmax, self.cmax).astype(np.int8)
            self.last_writes = wrote
        return self

    def scores(self, x, bs=2000):
        ar = np.arange(self.N)
        return np.concatenate([self.mem[:, ar[None, :], self.addr(x[i:i + bs])[0]].astype(np.int32).sum(2).T
                               for i in range(0, len(x), bs)])

    def votes(self, x, b, bs=2000):
        out = []
        for i in range(0, len(x), bs):
            a = self.addr(x[i:i + bs])
            hit = self.mem[:, np.arange(self.N)[None, None, :], a].min(1)    # (C, B, N) lookups, min over k
            out.append((hit >= b).sum(2).T)                                  # count recognising neurons
        return np.concatenate(out)

    def predict(self, x, b):
        return self.votes(x, b).argmax(1)

    def merge(self, other):                                                  # memory transfer: add the counts
        m = Cortex.__new__(Cortex); m.__dict__.update(self.__dict__)
        lo = -self.cmax if self.mem.dtype == np.int8 else 0
        m.mem = np.clip(self.mem.astype(np.int32) + other.mem, lo, self.cmax).astype(self.mem.dtype)
        return m

    def bits(self):
        return self.mem.size * (int(np.ceil(np.log2(self.cmax + 1))) + (self.mem.dtype == np.int8))
