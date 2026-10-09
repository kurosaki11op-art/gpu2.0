"""Build, simulate and check SPARK core v0 against the golden model.

Usage: python3 hw/run_sim.py            (runs all experiment configs)
Writes hw/results/sim_results.md and hw/results/sim_results.csv.
"""
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
RES = os.path.join(HERE, "results")
sys.path.insert(0, os.path.join(HERE, "golden"))
import spark_golden as sg  # noqa: E402

CONFIGS = [
    ("dense (GPU-style, every input)", dict(sparse=0)),
    ("event-driven (skip silent)", dict(sparse=1)),
    ("event-driven + change-only", dict(sparse=1, delta=1)),
    ("event-driven + early exit", dict(sparse=1, exit_en=1, exit_th=64)),
    ("event-driven + recall", dict(sparse=1, recall=1, conf_th=1)),
    ("event-driven + energy cap 16", dict(sparse=1, cap=16)),
    ("all think-less, always on (change-only + exit + recall)",
     dict(sparse=1, delta=1, exit_en=1, exit_th=64, recall=1, conf_th=1)),
    ("ADAPTIVE controller (recall + chooses change-only/full + adaptive exit)",
     dict(sparse=1, adapt=1, exit_en=1, exit_th=64, recall=1, conf_th=1)),
    ("ADAPTIVE controller, exit always succeeds (stress test)",
     dict(sparse=1, adapt=1, exit_en=1, exit_th=-1000000, recall=1, conf_th=1)),
]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        raise SystemExit(f"failed: {cmd}")
    return r.stdout


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    wts = sg.Weights()
    wts.export_hex(BUILD)
    data = sg.stim_text()
    with open(os.path.join(BUILD, "stim.hex"), "w") as f:
        f.write("\n".join(f"{b:02x}" for b in data) + "\n")
    sh("iverilog -g2012 -o sim.vvp ../rtl/spark_ram.v ../rtl/spark_core.v ../tb/tb_spark_core.v",
       BUILD)

    rows = []
    for name, ov in CONFIGS:
        cfg = sg.Cfg(**ov)
        g = sg.Golden(wts, cfg)
        gold = [g.step(b) for b in data]
        args = (f"+sparse={cfg.sparse} +delta={cfg.delta} +exit={cfg.exit_en} "
                f"+exit_th={cfg.exit_th} +recall={cfg.recall} +conf_th={cfg.conf_th} "
                f"+cap={cfg.cap} +adapt={cfg.adapt} +n={len(data)}")
        sh(f"vvp -n sim.vvp {args}", BUILD)
        rtl = [list(map(int, ln.split())) for ln in open(os.path.join(BUILD, "rtl_out.txt"))]
        mism = 0
        for go, r in zip(gold, rtl):
            exp = [go["pred"], go["path"]] + go["ev"] + go["proc"]
            if exp != r[:10]:
                mism += 1
        n = len(rtl)
        tot = lambda i: sum(r[i] for r in rtl)
        paths = [sum(1 for r in rtl if r[1] == p) for p in range(3)]
        rows.append(dict(
            config=name, tokens=n, mismatches=mism + abs(len(gold) - n),
            cycles_per_token=tot(10) / n, weight_reads_per_token=tot(11) / n,
            engine_cycles=tot(12) / n, scan_cycles=tot(13) / n, post_cycles=tot(14) / n,
            recall_cycles=tot(15) / n,
            events_per_token=sum(sum(r[6:10]) for r in rtl) / n,
            full=paths[0], early_exit=paths[1], recall=paths[2],
            cfg=json.dumps(ov)))
        print(f"{name:48s} mismatches={rows[-1]['mismatches']:4d} "
              f"cycles/token={rows[-1]['cycles_per_token']:9.1f} "
              f"weight reads/token={rows[-1]['weight_reads_per_token']:8.1f}")

    base = rows[0]
    with open(os.path.join(RES, "sim_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(RES, "sim_results.md"), "w") as f:
        f.write("# SPARK core v0 — simulation results (MEASURED in RTL simulation)\n\n")
        f.write(f"Input: {len(data)} bytes of Python-like text with repeated passages. "
                "Demo weights (random, sparse int4), not trained L weights.\n"
                "Every configuration is checked token-by-token against the bit-exact golden "
                "model (prediction, path and per-stage event counts).\n\n")
        f.write("| Configuration | Golden mismatches | Cycles/token | vs dense | Weight words read/token | vs dense | Events/token | Paths full / exit / recall |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['config']} | {r['mismatches']} | {r['cycles_per_token']:.0f} | "
                    f"{base['cycles_per_token'] / r['cycles_per_token']:.1f}x fewer | "
                    f"{r['weight_reads_per_token']:.0f} | "
                    f"{base['weight_reads_per_token'] / max(r['weight_reads_per_token'], 1e-9):.1f}x fewer | "
                    f"{r['events_per_token']:.1f} | {r['full']} / {r['early_exit']} / {r['recall']} |\n")
    print("wrote", os.path.join(RES, "sim_results.md"))


if __name__ == "__main__":
    main()
