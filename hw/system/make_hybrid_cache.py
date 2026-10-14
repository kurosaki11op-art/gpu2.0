"""Cache the hybrid's per-byte predictions (mode 0 and mode 2) on the 5 documents for close_gap.py."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:2]
src = open(os.path.join(HERE, "paired_stats.py")).read().split("rng = np.random")[0]
exec(compile(src, "paired_stats_head", "exec"))
out = {}
for name, (text, wdir) in docs.items():
    for mode in (0, 2):
        out[f"{name}_m{mode}"] = hybrid(text, wdir, mode)[0]
    print(name, flush=True)
np.savez(os.path.join(HERE, "out", "hybrid_preds.npz"), **out)
