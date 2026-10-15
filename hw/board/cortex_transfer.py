#!/usr/bin/env python3
"""Memory transfer demo with ONE board (or the emulator): the chip learns digits 0-4, its memory is saved to a file;
the chip is wiped and learns 5-9, saved again; the two memories are merged on the PC (tables added, dream counts added)
and loaded back; one self-regulated night; then it is tested on all ten digits.
--handover: instead of merging, the saved memory of 0-4 is loaded into the wiped chip, which then learns 5-9 itself
(sequential transfer). In simulation this beats the merge on all three tasks (experiments/month4/merge_variants.md).

  python cortex_transfer.py --dry-run --per-class 300 --data D:\\cortex_data
  python cortex_transfer.py --port COM5 --per-class 300 --data D:\\cortex_data
  python cortex_transfer.py --port COM5 --per-class 300 --data D:\\cortex_data --handover
Memories are saved as memory_0to4.npz, memory_5to9.npz, memory_merged.npz (copy them to another board to transfer)."""
import argparse, time
import numpy as np
from cortex_host import Board, Emu, SEED_LANES, mnist, run_stage, merge, night
from feature_layer import Features


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--per-class", type=int, default=300); ap.add_argument("--test", type=int, default=1000)
    ap.add_argument("--handover", action="store_true", help="load the 0-4 memory and learn 5-9 on top (no merge)")
    a = ap.parse_args()
    xtr, ytr, xte, yte = mnist(a.data)
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    tst = np.random.RandomState(0).choice(len(yte), a.test, replace=False); cte, yt = enc(xte[tst]), yte[tst]
    dev = Emu(cte.shape[1]) if a.dry_run else Board(a.port, a.baud)
    dev.seed(SEED_LANES)
    score = lambda: float(np.mean([dev.predict(cte[j]) == yt[j] for j in range(len(yt))]))
    mems = {}
    for name, cls in (("0to4", range(5)), ("5to9", range(5, 10))):
        t0 = time.time(); nt = dev.night_total; dev.clear(); known = set()
        if a.handover and name == "5to9":
            dev.load(mems["0to4"]); dev.night_total = nt; known = set(np.where(mems["0to4"]["known"])[0].tolist())
        sel = np.concatenate([np.where(ytr == c)[0][:a.per_class] for c in cls]); sel = sel[np.random.RandomState(len(name)).permutation(len(sel))]
        run_stage(dev, enc(xtr[sel]), ytr[sel], known)
        mems[name] = dev.export(); np.savez_compressed(f"memory_{name}.npz", **mems[name])
        print(f"chip learned digits {name}: accuracy on all 10 digits {score():.3f}  (saved memory_{name}.npz, {time.time()-t0:.0f}s)")
    if a.handover:
        print(f"hand-over done: memory of 0-4 loaded, then 5-9 learned on top: {score():.3f} on all 10 digits")
        return
    m = merge(mems["0to4"], mems["5to9"]); np.savez_compressed("memory_merged.npz", **m)
    dev.clear(); dev.load(m)
    print(f"merged memory loaded, before sleep: {score():.3f}")
    n = night(dev, set(np.where(m["known"])[0].tolist()))
    print(f"after one night ({n} dreams): {score():.3f} on all 10 digits")


if __name__ == "__main__":
    main()
