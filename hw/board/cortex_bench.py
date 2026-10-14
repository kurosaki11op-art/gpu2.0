#!/usr/bin/env python3
"""Month-4 power and speed benchmark for SPARK Cortex on the Tang Nano 20K (works with a USB power meter read by eye).

Runs fixed-length phases and tells you when to read the meter:
  idle      board configured, no traffic                     -> P_idle
  link      ping loop (UART traffic, no learning or deciding) -> P_link
  decide    PREDICT loop on test images                       -> P_decide, decisions per second
  learn     LEARN loop on training images (count + practise)  -> P_learn, examples per second
  dream     DREAM loop (generate + practise)                  -> P_dream, dreams per second
Energy per operation above the link cost: E = (P_phase - P_link) / (operations per second).
Results go to cortex_bench_<time>.csv; type the meter readings when asked (or press Enter to skip).

  python cortex_bench.py --port COM5 --data D:\\cortex_data [--seconds 30] [--onchip-encode]
  python cortex_bench.py --dry-run           # walks through the phases on the emulator (no power numbers)"""
import argparse, csv, os, time
import numpy as np
from cortex_host import Board, Emu, SEED_LANES, mnist
from feature_layer import Features


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--seconds", type=float, default=30.0); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--onchip-encode", action="store_true")
    a = ap.parse_args()
    xtr, ytr, xte, yte = mnist(a.data)
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    onchip = a.onchip_encode and not a.dry_run
    dev = Emu(4608) if a.dry_run else Board(a.port, a.baud, onchip)
    if onchip:
        dev.detectors(fes)
    dev.seed(SEED_LANES); dev.clear()
    for c in range(10):
        dev.known(c)
    tr_rows = (xtr[:3000] if onchip else enc(xtr[:3000])); te_rows = (xte[:1000] if onchip else enc(xte[:1000]))
    for i in range(300):                                                     # some knowledge so practise is realistic
        dev.learn(int(ytr[i]), tr_rows[i])
    rows = []

    def phase(name, op):
        input(f"\n[{name}] press Enter to start ({a.seconds:.0f} s); read the power meter during the run")
        n, t0 = 0, time.time()
        while time.time() - t0 < a.seconds:
            op(n); n += 1
        dt = time.time() - t0
        p = input(f"[{name}] {n} operations in {dt:.1f} s ({n / dt:.1f}/s). Meter reading in watts (Enter = skip): ").strip()
        rows.append({"phase": name, "ops": n, "seconds": round(dt, 2), "ops_per_s": round(n / dt, 2), "watts": p})

    phase("idle", lambda n: time.sleep(0.05))
    phase("link", lambda n: dev.ping())
    phase("decide", lambda n: dev.predict(te_rows[n % len(te_rows)]))
    phase("learn", lambda n: dev.learn(int(ytr[n % 3000]), tr_rows[n % 3000]))
    phase("dream", lambda n: dev.dream(n % 10))
    name = time.strftime("cortex_bench_%Y%m%d_%H%M%S.csv")
    with open(name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"\nsaved {name}")
    pl = next((float(r["watts"]) for r in rows if r["phase"] == "link" and r["watts"]), None)
    for r in rows:
        if r["phase"] in ("decide", "learn", "dream") and r["watts"] and pl is not None:
            e = (float(r["watts"]) - pl) / r["ops_per_s"]
            print(f"{r['phase']:6s}: {e * 1e6:.1f} uJ per operation above the link cost (MEASURED, board level)")


if __name__ == "__main__":
    main()
