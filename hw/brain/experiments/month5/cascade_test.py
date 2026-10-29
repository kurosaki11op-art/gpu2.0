"""29 Oct 2026, SIMULATED accuracy, ESTIMATED energy (operation counts, int8 multiply-add 0.2 pJ, 45 nm reference). CASCADE: the chip answers the images it is sure about; the least-sure share f is sent to a stronger fallback (here the strong reference CNN standing in for a GPU or a person). Compared with a CNN-only cascade (small CNN first, strong CNN on the least-sure share) and with the strong CNN alone.
Energy per image = first stage + f x fallback. Chip first stage 49 nJ (L + L Deep, project estimate); small CNN 3.87 M multiply-adds = 0.77 uJ; strong CNN about 19.0 M multiply-adds = 3.8 uJ (multiplies only, no memory traffic, so these are lower bounds for the CNNs)."""
import sys
sys.argv = ["x"]; sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
import numpy as np, ldeep_ref as R
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SP + "deep_test_all.npz"); X = np.ascontiguousarray(z["X"], np.uint8); y = z["y"].astype(np.int64); rr, S, pp = R.run(X); srt = np.sort(S, 1); cm = (srt[:, -1] - srt[:, -2]).astype(np.float64)
Ls, Lg = np.load(SP + "logits_small.npy"), np.load(SP + "logits_strong.npy"); lm = lambda lg: (lambda s: s[:, -1] - s[:, -2])(np.sort(lg, 1)); ps, pg = Ls.argmax(1), Lg.argmax(1)
E_CHIP, E_SMALL, E_STRONG = 0.049, 0.77, 3.8   # microjoule per image
def cascade(first_pred, first_conf, f): n = len(y); fl = np.argsort(first_conf, kind="stable")[: int(round(f * n))]; out = first_pred.copy(); out[fl] = pg[fl]; return (out == y).mean()
print("strong CNN alone: accuracy %.4f, %.2f uJ per image (multiplies only)" % ((pg == y).mean(), E_STRONG))
print("%-8s | %-34s | %-34s" % ("flagged", "chip -> strong CNN", "small CNN -> strong CNN"))
print("%-8s | %-12s %-10s %-10s | %-12s %-10s %-10s" % ("share", "accuracy", "uJ/image", "vs strong", "accuracy", "uJ/image", "vs strong"))
for f in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30):
    a1 = cascade(pp, cm, f); e1 = E_CHIP + f * E_STRONG; a2 = cascade(ps, lm(Ls), f); e2 = E_SMALL + f * E_STRONG
    print("%-8s | %-12.4f %-10.3f %-10s | %-12.4f %-10.3f %-10s" % ("%d%%" % round(100 * f), a1, e1, "%.1fx less" % (E_STRONG / e1), a2, e2, "%.1fx less" % (E_STRONG / e2)))
