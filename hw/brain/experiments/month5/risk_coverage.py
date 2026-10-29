"""28 Oct 2026, SIMULATED. Selective answering: the chip returns its answer only when the margin of its FINAL scores (top minus runner-up, after L Deep where it was woken) is above a threshold, and flags the rest for a fallback (a person, a GPU, or a re-look).
Reports accuracy on the answered images and the share flagged (coverage = share answered). No extra energy: the margin is already computed by the dispatcher/argmax. Integer scores from the RTL memory files via ldeep_ref, all 10,000 test images."""
import sys
sys.argv = ["x"]; sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
import numpy as np, ldeep_ref as R
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = np.ascontiguousarray(z["X"], np.uint8), z["y"].astype(np.int64)
rr, S, pp = R.run(X); srt = np.sort(S, 1); m = (srt[:, -1] - srt[:, -2]).astype(np.float64); ok = pp == y; o = np.argsort(-m, kind="stable")
print("all images answered: accuracy %.4f (error %.2f%%)" % (ok.mean(), 100 * (1 - ok.mean())))
print("%-18s %-12s %-14s %-s" % ("share flagged", "answered", "accuracy", "errors left among answered (per 1,000 answered)"))
for f in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
    k = int(round((1 - f) * len(y))); a = ok[o[:k]].mean()
    print("%-18s %-12d %-14.4f %.0f" % ("%d%%" % round(100 * f), k, a, 1000 * (1 - a)))
tot_err = (~ok).sum(); fl = o[int(0.8 * len(y)):]; print("the 20%% flagged images hold %.0f%% of all errors" % (100 * (~ok[fl]).sum() / tot_err))
