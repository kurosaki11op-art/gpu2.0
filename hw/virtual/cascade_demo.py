#!/usr/bin/env python3
"""CASCADE DEMO (30 Oct 2026, SIMULATED accuracy, ESTIMATED energy). End to end: image -> L chip (L Cortex + L Deep, with its reject flag) -> if flagged, a stronger fallback (a reference CNN standing in for a GPU or a person) -> final answer, with the energy accounting.
Two modes:
  default      the chip's bit-exact reference model (hw/brain/experiments/month5/ldeep_ref.py, checked identical to the RTL on all 10,000 images) over the whole Fashion-MNIST test set;
  --rtl N      additionally runs the real RTL (hw/rtl/deep/l_cortex_deep.v, with its reject_t input and flag output, through run_check_full.py) on the first N images and cascades the RTL's own answers and flags.
The reject threshold is calibrated the way a host would, on UNLABELLED data: the first 2,000 test images (margins only, no labels) set the threshold for the requested flagged share, and every accuracy figure is then computed on the other 8,000 images (the whole set is also shown).
Fallback: the strong reference CNN (4 conv layers, shift and flip augmentation, 12 epochs; see hw/brain/experiments/month5/cnn_confidence.py), logits stored in hw/virtual/results/fallback_cnn_logits.npy.
Energy per image (ESTIMATED, operation counts at the project's 45 nm constants, lower bounds for the CNN because only multiplies and a traffic variant are counted): chip first stage 0.049 uJ (L + L Deep by operation count; its layout energy is higher, see the sensitivity table), strong CNN 3.8 uJ (multiplies only) or 4.18 uJ (with weight and activation traffic, weights shared over a batch of 64).
usage: python cascade_demo.py [--flag-share 0.15] [--rtl N]      outputs: hw/virtual/results/cascade_demo.{json,csv,png}"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results"); DEEP = os.path.join(HERE, "..", "rtl", "deep")
sys.path.insert(0, os.path.join(HERE, "..", "brain", "experiments", "month5"))
args = sys.argv[1:]; SHARE = float(args[args.index("--flag-share") + 1]) if "--flag-share" in args else 0.15; NRTL = int(args[args.index("--rtl") + 1]) if "--rtl" in args else 0
SCR = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SCR + "deep_test_all.npz"); X, y = np.ascontiguousarray(z["X"], np.uint8), z["y"].astype(np.int64); n = len(y)
LG = os.path.join(RES, "fallback_cnn_logits.npy")
if not os.path.exists(LG):
    if not os.path.exists(SCR + "logits_strong.npy"): sys.exit("fallback logits missing: run hw/brain/experiments/month5/cnn_confidence.py first")
    np.save(LG, np.load(SCR + "logits_strong.npy"))
fb = np.load(LG).argmax(1); fb_ok = fb == y
import ldeep_ref as R
rr, S, pp = R.run(X); srt = np.sort(S, 1); mrg = (srt[:, -1] - srt[:, -2]).astype(np.int64); chip_ok = pp == y
E_CHIP, E_CNN, E_CNN_T = 0.049, 3.8, 4.18      # uJ per image
CAL = np.arange(n) < 2000; EV = ~CAL
def calibrate(share): return int(np.floor(np.quantile(mrg[CAL], share)))   # margins only, no labels
def cascade(T, mask):
    flag = mrg <= T; final = np.where(flag, fb, pp); ok = final == y
    return flag, final, ok
T = calibrate(SHARE); flag, final, ok = cascade(T, EV)
print("L chip + fallback CNN, cascade demo (SIMULATED accuracy, ESTIMATED energy)")
print("reject threshold %d (the %.0f%% quantile of the margins of the first 2,000 unlabelled images); evaluation on the other %d images\n" % (T, 100 * SHARE, EV.sum()))
fs = flag[EV].mean(); a_chip = chip_ok[EV].mean(); a_cnn = fb_ok[EV].mean(); a_cas = ok[EV].mean(); a_ans = chip_ok[EV & ~flag].mean(); a_fl_chip = chip_ok[EV & flag].mean(); a_fl_cnn = fb_ok[EV & flag].mean()
e_cas, e_cas_t = E_CHIP + fs * E_CNN, E_CHIP + fs * E_CNN_T
print("%-46s %s" % ("flagged share (sent to the fallback)", "%.1f%%" % (100 * fs)))
print("%-46s %.4f   (%.2f uJ per image)" % ("chip alone, every image answered", a_chip, E_CHIP))
print("%-46s %.4f   (%.2f uJ multiplies only, %.2f with traffic)" % ("strong CNN alone", a_cnn, E_CNN, E_CNN_T))
print("%-46s %.4f   (%.3f uJ multiplies only, %.3f with traffic)" % ("CASCADE: chip answers, fallback on flagged", a_cas, e_cas, e_cas_t))
print("%-46s %.4f vs %.4f (chip) and %.4f (fallback) on those images" % ("on the flagged images: cascade uses the fallback", a_fl_cnn, a_fl_chip, a_fl_cnn))
print("%-46s %.4f" % ("accuracy of the chip on the images it answers", a_ans))
print("%-46s %.1fx (multiplies only) / %.1fx (with traffic)\n" % ("energy of the cascade against the CNN alone", E_CNN / e_cas, E_CNN_T / e_cas_t))
print("sensitivity to the chip's first-stage energy (the layout energy of Cortex is estimated at 20 to 28 times its operation count):")
print("  %-26s %s" % ("first stage uJ per image", "  ".join("%7.3f" % e for e in (0.049, 0.3, 1.0))))
print("  %-26s %s" % ("cascade uJ per image", "  ".join("%7.3f" % (e + fs * E_CNN) for e in (0.049, 0.3, 1.0))))
print("  %-26s %s\n" % ("times less than CNN alone", "  ".join("%6.1fx" % (E_CNN / (e + fs * E_CNN)) for e in (0.049, 0.3, 1.0))))
print("threshold sweep (evaluation images only):")
print("  %-8s %-10s %-10s %-12s %-14s %s" % ("flagged", "threshold", "cascade", "chip answered", "uJ/image (mult.)", "vs CNN alone"))
sweep = []
for sh in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 1.0):
    t = calibrate(sh) if sh < 1.0 else int(mrg.max()); fl, fn, o = cascade(t, EV); f = fl[EV].mean(); e = E_CHIP + f * E_CNN; sweep.append((sh, t, f, o[EV].mean(), chip_ok[EV & ~fl].mean() if (EV & ~fl).any() else float("nan"), e))
    print("  %-8s %-10d %-10.4f %-12.4f %-14.3f %.1fx less" % ("%d%%" % round(100 * f), t, o[EV].mean(), sweep[-1][4], e, E_CNN / e))
os.makedirs(RES, exist_ok=True)
with open(os.path.join(RES, "cascade_demo.csv"), "w") as f:
    f.write("index,label,chip_pred,routed_to_deep,margin,flagged,fallback_pred,final_pred,final_correct\n")
    for i in range(n): f.write("%d,%d,%d,%d,%d,%d,%d,%d,%d\n" % (i, y[i], pp[i], rr[i], mrg[i], int(flag[i]), fb[i], final[i], int(ok[i])))
summary = {"flag_share_requested": SHARE, "threshold": T, "calibration_images": 2000, "evaluation_images": int(EV.sum()), "flagged_share": float(fs), "chip_alone": float(a_chip), "strong_cnn_alone": float(a_cnn), "cascade": float(a_cas),
           "chip_accuracy_on_answered": float(a_ans), "energy_uJ_cascade_multiplies_only": e_cas, "energy_uJ_cnn_multiplies_only": E_CNN, "energy_uJ_cascade_with_traffic": e_cas_t, "energy_uJ_cnn_with_traffic": E_CNN_T, "sweep": [list(map(float, s)) for s in sweep], "label": "SIMULATED accuracy, ESTIMATED energy"}
# ---- optional: the real RTL in the loop on the first N images
if NRTL:
    print("\nRTL in the loop: running l_cortex_deep.v (reject_t and flag in the RTL) on the first %d images through run_check_full.py ..." % NRTL, flush=True)
    r = subprocess.run([sys.executable, os.path.join(DEEP, "run_check_full.py"), "/tmp/fashion", str(NRTL)], capture_output=True, text=True, cwd=DEEP); print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])
    rows = [list(map(int, l.split())) for l in open(os.path.join(DEEP, "out_full.txt")).read().strip().split("\n")]; pr = np.array([g[11] for g in rows]); fr = np.array([g[17] for g in rows]).astype(bool); yy = y[:NRTL]
    fin = np.where(fr, fb[:NRTL], pr); same = bool((pr == pp[:NRTL]).all())
    print("RTL on %d images: chip alone %.4f, flagged %d (%.1f%%), chip on the answered %.4f, CASCADE with the RTL's own flags %.4f, strong CNN alone %.4f; RTL predictions identical to the model's: %s" % (NRTL, (pr == yy).mean(), fr.sum(), 100 * fr.mean(), (pr == yy)[~fr].mean(), (fin == yy).mean(), fb_ok[:NRTL].mean(), same))
    summary["rtl"] = {"images": NRTL, "chip_alone": float((pr == yy).mean()), "flagged": int(fr.sum()), "cascade": float((fin == yy).mean()), "predictions_identical_to_model": same}
json.dump(summary, open(os.path.join(RES, "cascade_demo.json"), "w"), indent=1)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4.4)); ax.plot([s[5] for s in sweep], [s[3] * 100 for s in sweep], "o-", color="#1f77b4", label="chip + fallback cascade (flagged share labelled)")
for s in sweep[:-1]: ax.annotate("%d%%" % round(100 * s[2]), (s[5], s[3] * 100), textcoords="offset points", xytext=(4, -10), fontsize=8)
ax.plot([E_CHIP], [a_chip * 100], "s", color="#2ca02c", label="chip alone"); ax.plot([E_CNN], [a_cnn * 100], "^", color="#d62728", label="strong CNN alone (multiplies only)")
ax.set_xscale("log"); ax.set_xlabel("energy per image, microjoule (ESTIMATED, operation counts)"); ax.set_ylabel("accuracy on the evaluation images, %"); ax.set_title("Chip-first cascade: accuracy against energy (SIMULATED / ESTIMATED)"); ax.grid(alpha=.3); ax.legend(fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(RES, "cascade_demo.png"), dpi=130)
print("\nwrote hw/virtual/results/cascade_demo.json, cascade_demo.csv (one row per image) and cascade_demo.png")
