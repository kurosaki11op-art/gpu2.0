"""28 Oct 2026. DISPATCH TESTS (founder: Cortex first, predict the need early, wake the bigger layer only when needed). SIMULATED accuracy and rates on Fashion-style test set (10,000 images) with the shipped L code (4,608 bits) and shipped counting table; ESTIMATED energy/time.
(a) Early partial margin: read the code bits in image order (position-major, then channel) or random order, stop after a fraction f of the bits, take the margin of the partial scores. Does the partial margin predict which images the FINAL shipped margin would route (least-sure share r)? Report missed wakes (routed images not woken) and false wakes (woken images that were not routed) when waking the least-sure share w of the partial margins. Also early exit: the accuracy of the partial answer on the images NOT woken.
(b) and (c) are arithmetic on the measured rates (see dispatch_tests_cost() below), with ASSUMED wake energy, leakage and retention figures."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ytr, yte, ctr, cte, train_table
T = train_table(ctr, ytr).astype(np.int32); C = cte.astype(np.int32); F = 32
S0 = C @ T; srt = np.sort(S0, 1); m0 = srt[:, -1] - srt[:, -2]; p0 = S0.argmax(1); print("shipped: acc %.4f" % (p0 == yte).mean(), flush=True)
cols = np.arange(4608); ch, pos, d = cols // 1152, (cols % 1152) // F, cols % F
orders = {"image order (position-major)": np.lexsort((ch, pos)), "random order": np.random.RandomState(0).permutation(4608)}
def margin(S): s = np.sort(S, 1); return s[:, -1] - s[:, -2]
res = {}
for r in (0.1, 0.2):
    route = m0 <= np.quantile(m0, r)
    print("\n== final route share r = %.0f%% (shipped margin rule), %d images ==" % (100 * r, route.sum()))
    print("%-30s %5s %8s | %-28s | %-28s | %s" % ("order", "f", "bits/img", "wake w=r: missed / false", "wake w=2r: missed / false", "early-exit acc on not-woken (w=2r) vs final answer"))
    for on, o in orders.items():
        for f in (0.1, 0.25, 0.5, 0.75):
            n = int(4608 * f); idx = o[:n]; S = C[:, idx] @ T[idx]; mf = margin(S) / f; row = []
            for w in (r, 2 * r):
                wake = mf <= np.quantile(mf, w); missed = (route & ~wake).sum() / route.sum(); false = (wake & ~route).sum() / wake.sum(); row.append((missed, false, wake))
            nw = ~row[1][2]; acc_part = (S.argmax(1)[nw] == yte[nw]).mean(); acc_fin = (p0[nw] == yte[nw]).mean()
            print("%-30s %5.2f %8d | %6.1f%% / %6.1f%%            | %6.1f%% / %6.1f%%            | %.4f vs %.4f" % (on, f, n, 100 * row[0][0], 100 * row[0][1], 100 * row[1][0], 100 * row[1][1], acc_part, acc_fin), flush=True)
            res[(r, on, f)] = row
print("\n(b),(c) COST ARITHMETIC (ESTIMATED; assumed inputs listed): Deep-class layer: stage-2 energy 10.7 nJ per woken image (matrix-free second pass, cost model of earlier notes), Cortex full 29.9 nJ; memory of the woken layer 262 KB (Deep 227+35 KB), leakage 60 pW/bit powered, retention saves 98% (claim of a retention-SRAM paper found by search, not verified), decision time 6 us (pipelined core, 264 cycles at 43 MHz).")
bits = 262 * 1024 * 8; P_idle = bits * 60e-12; P_save = 0.98 * P_idle
print("  powered-idle leakage of the woken layer's memory %.3f mW; saved by retention %.3f mW" % (P_idle * 1e3, P_save * 1e3))
print("  BREAK-EVEN idle time t = E_wake / P_saved:")
for W in (0.1, 1.0, 10.0, 100.0): print("    wake energy %6.1f nJ -> break-even %9.1f us" % (W, W * 1e-9 / P_save * 1e6))
print("  Mean gap between wake requests = decision time / share woken:")
for w in (0.05, 0.1, 0.2, 0.4): print("    share woken %4.0f%% -> %6.0f us between wakes (pays only if wake energy small enough for the break-even above to be shorter)" % (100 * w, 6.0 / w))
print("  NET ENERGY per image for 'always on' vs 'gated with wake energy W', wake share w, false-wake rate fw (extra wakes among those woken):")
for w in (0.1, 0.2, 0.4):
    for W in (1.0, 10.0, 100.0):
        e_on = 29.9 * 1 + w * 10.7 + 0.0; idle_leak_nj = P_idle * (6e-6) * 1e9 * (1 - w); e_gate = 29.9 + w * (10.7 + W) + 0.02 * P_idle * 6e-6 * 1e9 * (1 - w)
        print("    w=%2.0f%% W=%5.1f nJ: always-on %.2f nJ, gated %.2f nJ" % (100 * w, W, e_on + idle_leak_nj, e_gate))
