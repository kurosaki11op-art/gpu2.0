"""Many users, one chip: do tables SHARED by all streams beat PRIVATE tables of the same total memory?
Each stream keeps its own 6-byte history (per-user state); only the hashed tables and the order-1 table are shared or split.
Streams are interleaved byte by byte (concurrent users). Configurations, all v2 lookup design (2-way, order-1 fallback):
  private-equal : each of S streams gets 1/S of the memory (2^(TB - log2 S) sets per table)
  shared        : one table set of 2^TB sets used by all streams
  private-full  : each stream gets the full 2^TB sets (S times the memory; upper reference)
Mixes: related (S code streams from different files of one corpus), unrelated (half code, half prose).
usage: python multistream.py <prose_train.txt>"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
from lookup_ref import LookupCoreV2, slot_tag, ORDERS  # noqa
import train_spark_v0 as tr  # noqa


class SharedV2(LookupCoreV2):
    """LookupCoreV2 with per-stream (hist, prev) and shared tables."""
    def __init__(self, tb, S):
        super().__init__(tb); self.ctx = [(0, None)] * S

    def step_s(self, sid, b):
        self.hist, self.prev = self.ctx[sid]
        r = self.step(b)
        self.ctx[sid] = (self.hist, self.prev)
        return r


def run(streams, mode, tb, S):
    L = min(len(s) for s in streams)
    if mode == "shared":
        core = SharedV2(tb, S); step = core.step_s
    else:
        cores = [LookupCoreV2(tb if mode == "private-full" else tb - int(np.log2(S))) for _ in range(S)]
        step = lambda sid, b: cores[sid].step(b)  # noqa: E731
    ok = np.zeros((S, L - 1), bool); last = [None] * S
    for i in range(L):
        for sid in range(S):
            b = streams[sid][i]
            if last[sid] is not None: ok[sid, i - 1] = last[sid] == b
            last[sid] = step(sid, b)[0]
    return ok.mean()


S, N, TB = 8, 25000, 11
code = bytes(tr.load_corpus(1_200_000)); prose = open(sys.argv[1], "rb").read()
code_streams = [code[k * 150000:k * 150000 + N] for k in range(S)]
prose_streams = [prose[k * 400000:k * 400000 + N] for k in range(S)]
mixes = {"related (8 code files)": code_streams, "unrelated (4 code + 4 prose)": code_streams[:4] + prose_streams[:4],
         "prose (8 book chunks)": prose_streams}
for name, st in mixes.items():
    r = {m: run(st, m, TB, S) for m in ("private-equal", "shared", "private-full")}
    print(f"{name:30s} private, same total memory {r['private-equal']:.2%} | shared {r['shared']:.2%} | private, 8x memory {r['private-full']:.2%}", flush=True)
