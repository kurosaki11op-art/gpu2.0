#!/usr/bin/env python3
"""Host for the ESP32 image server (hw/mcu/esp32_serve): runs the Fashion-MNIST test set through the L algorithm ON THE ESP32 and cascades the flagged images to a stronger fallback (the strong reference CNN, its stored logits).
Steps: (1) the first CAL images run with the reject threshold at 0; the margins the ESP32 returns (no labels used) set the threshold for the requested flagged share; (2) the threshold is sent to the board; (3) the remaining images run, the board flags the unsure ones, the fallback answers those.
Reports: bit-exactness against the reference model (all predictions, the routed bit, the margin), accuracy of the algorithm on the hardware, the flagged share, the cascade accuracy, the board's compute time and the wall time per image. Everything here is MEASURED on the board except the fallback's logits (stored) and the model (the reference).
usage: python serve_host.py --port COM7 [--baud 921600] [--n 10000] [--cal 2000] [--flag-share 0.15] [--data DIR]       (DIR holds the Fashion-MNIST .gz files, default ~/fashion)
       python serve_host.py --exec ./shim_binary ...     runs a process instead of a serial port (used to test the protocol on a PC)
needs: pip install numpy pyserial"""
import argparse, gzip, json, os, struct, subprocess, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--port"); ap.add_argument("--exec"); ap.add_argument("--baud", type=int, default=921600); ap.add_argument("--n", type=int, default=10000); ap.add_argument("--cal", type=int, default=2000)
ap.add_argument("--flag-share", type=float, default=0.15); ap.add_argument("--data", default=os.path.join(os.path.expanduser("~"), "fashion")); a = ap.parse_args()
def idx(path):
    d = gzip.open(path, "rb").read(); magic = struct.unpack(">I", d[:4])[0]; nd = magic & 0xFF; dims = struct.unpack(">" + "I" * nd, d[4:4 + 4 * nd]); return np.frombuffer(d, np.uint8, offset=4 + 4 * nd).reshape(dims)
X = idx(os.path.join(a.data, "fashion-t10k-images-idx3-ubyte.gz")).reshape(-1, 784); y = idx(os.path.join(a.data, "fashion-t10k-labels-idx1-ubyte.gz")).astype(np.int64); N = min(a.n, len(y)); CAL = min(a.cal, N // 2)
ref = np.load(os.path.join(HERE, "model_expected_10k.npz")); fb = np.load(os.path.join(HERE, "..", "virtual", "results", "fallback_cnn_logits.npy")).argmax(1)
class Port:   # one interface over a serial port or a child process
    def __init__(self):
        if a.exec: self.p = subprocess.Popen(a.exec.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0); self.r, self.w = self.p.stdout, self.p.stdin
        else:
            import serial; self.s = serial.Serial(a.port, a.baud, timeout=3); self.r = self.s; self.w = self.s
    def write(self, b): self.w.write(b); (self.s.flush() if not a.exec else None)
    def read(self, n):
        out = b""
        while len(out) < n:
            c = self.r.read(n - len(out))
            if not c: break
            out += c
        return out
    def readline(self): return self.r.readline()
port = Port()
def wait_banner():
    # opening the port usually resets the board, which then prints the banner by itself: wait for it first; ping only if it does not come
    for attempt in range(2):
        t0 = time.time()
        if attempt == 1: port.write(bytes([0xA8]))
        while time.time() - t0 < 4:
            l = port.readline()
            if b"L-SERVE READY" in l:
                if not a.exec: time.sleep(0.3); port.s.reset_input_buffer()    # discard anything else that arrived (a second banner)
                return
    sys.exit("no banner from the board: check the port, close the Serial Monitor, press EN on the board and try again")
wait_banner()
def set_reject(t): port.write(bytes([0xA6, t & 255, (t >> 8) & 255, (t >> 16) & 15])); r = port.read(1); assert r == b"\x5c", "no acknowledge for the reject threshold: %r" % r
def classify(i):
    port.write(bytes([0xA5]) + X[i].tobytes()); r = port.read(11)
    if len(r) != 11 or r[0] != 0x5A: sys.exit("bad reply for image %d: %r" % (i, r))
    return r[1], r[2] & 1, (r[2] >> 1) & 1, struct.unpack("<i", r[3:7])[0], struct.unpack("<I", r[7:11])[0]
pred = np.zeros(N, np.int64); routed = np.zeros(N, np.int64); flag = np.zeros(N, np.int64); mrg = np.zeros(N, np.int64); us = np.zeros(N, np.int64)
print("L algorithm on the ESP32, %d images (calibration %d, then evaluation), serial %s" % (N, CAL, "child process" if a.exec else "%s at %d baud" % (a.port, a.baud)), flush=True); t0 = time.time()
set_reject(0)
for i in range(CAL):
    pred[i], routed[i], flag[i], mrg[i], us[i] = classify(i)
    if i % 500 == 499: print("  calibration %d/%d" % (i + 1, CAL), flush=True)
T = int(np.floor(np.quantile(mrg[:CAL], a.flag_share))); set_reject(T); print("reject threshold %d (the %.0f%% quantile of the margins the board returned on %d unlabelled images)" % (T, 100 * a.flag_share, CAL), flush=True)
for i in range(CAL, N):
    pred[i], routed[i], flag[i], mrg[i], us[i] = classify(i)
    if i % 1000 == 999: print("  %d/%d  elapsed %.0f s" % (i + 1, N, time.time() - t0), flush=True)
wall = time.time() - t0; ev = np.arange(N) >= CAL; ok = pred == y[:N]; fl = flag.astype(bool); cas = np.where(fl, fb[:N], pred) == y[:N]
exact = bool((pred == ref["pred"][:N]).all() and (routed == ref["routed"][:N]).all() and (mrg == ref["margin"][:N]).all()); n_bad = int(((pred != ref["pred"][:N]) | (routed != ref["routed"][:N]) | (mrg != ref["margin"][:N])).sum())
res = {"images": N, "calibration_images": CAL, "reject_threshold": T, "identical_to_model": exact, "mismatching_images": n_bad, "accuracy_algorithm_all": float(ok.mean()), "accuracy_algorithm_eval": float(ok[ev].mean()), "routed_share": float(routed.mean()),
       "flagged_share_eval": float(fl[ev].mean()), "accuracy_on_answered_eval": float(ok[ev & ~fl].mean()), "accuracy_cascade_eval": float(cas[ev].mean()), "accuracy_fallback_alone_eval": float((fb[:N] == y[:N])[ev].mean()),
       "board_compute_ms_per_image": float(us.mean() / 1000), "wall_ms_per_image": 1000 * wall / N, "baud": None if a.exec else a.baud, "label": "MEASURED on the ESP32 (software); fallback = stored logits of the strong reference CNN"}
os.makedirs(os.path.join(HERE, "results"), exist_ok=True); json.dump(res, open(os.path.join(HERE, "results", "esp32_serve_run.json"), "w"), indent=1)
print("\nresults on %d images:" % N)
print("  predictions, routed bits and margins identical to the model on every image: %s (%d mismatching images)" % ("YES" if exact else "NO", n_bad))
print("  accuracy of the L algorithm on the ESP32: %.4f on all, %.4f on the evaluation images; routed to L Deep: %.1f%%" % (ok.mean(), ok[ev].mean(), 100 * routed.mean()))
print("  flagged %.1f%% of the evaluation images; accuracy on the answered (unflagged) images %.4f" % (100 * fl[ev].mean(), ok[ev & ~fl].mean()))
print("  CASCADE (ESP32 answers, fallback on the flagged): %.4f   fallback alone: %.4f" % (cas[ev].mean(), (fb[:N] == y[:N])[ev].mean()))
print("  board compute time %.2f ms per image; wall time %.1f ms per image (%.0f s in all)" % (us.mean() / 1000, 1000 * wall / N, wall))
print("wrote hw/mcu/results/esp32_serve_run.json (send me this file)")
