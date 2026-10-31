#!/usr/bin/env python3
"""M3 checks (31 Oct 2026): runs the tile_mm RTL (Icarus Verilog) on real INT8 weights of the M1 transformer and the M1 self-test, compares the accumulators with a numpy integer matrix product (bar M3-a),
the self-test dequantised result with the simulator's output, and the cycle counts with m*nb*k + pipeline (bar M3-b). usage: python m3_check.py WORKDIR (the M1 work directory with lm/ and selftest/)"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
W = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); res = {}
def manifest(d):
    out = {}
    for l in open(os.path.join(d, "manifest.txt")): p = l.split(); out[p[0]] = (int(p[1]), [int(x) for x in p[3:3 + int(p[2])]])
    return out
def tensor(d, name):
    off, dims = manifest(d)[name]; return np.fromfile(os.path.join(d, "tensors.bin"), np.float32, count=int(np.prod(dims)), offset=4 * off).reshape(dims)
def quant_w(w): sw = np.abs(w).max(0) / 127.0; sw[sw == 0] = 1.0; return np.round(w / sw).clip(-127, 127).astype(np.int64), sw.astype(np.float32)
def quant_a(a): m = np.abs(a).max(1, keepdims=True); sa = np.where(m > 0, m / 127.0, 1.0).astype(np.float32); return np.round(a / sa).clip(-127, 127).astype(np.int64), sa
def run_rtl(qa, qw, lanes):
    m, k = qa.shape; n = qw.shape[1]; nb = math.ceil(n / lanes); tmp = tempfile.mkdtemp(prefix="m3_", dir="/tmp"); words = []
    for b in range(nb):
        for s in range(k):
            col = np.zeros(lanes, np.int64); cols = qw[s, b * lanes:(b + 1) * lanes]; col[:len(cols)] = cols
            words.append("".join("%02x" % (int(v) & 0xFF) for v in col[::-1]))
    open(os.path.join(tmp, "wmem.hex"), "w").write("\n".join(words) + "\n"); open(os.path.join(tmp, "amem.hex"), "w").write("\n".join("%02x" % (int(v) & 0xFF) for v in qa.reshape(-1)) + "\n")
    subprocess.run(["iverilog", "-g2005", "-o", os.path.join(tmp, "sim"), "-Ptb_tile_mm.LANES=%d" % lanes, os.path.join(HERE, "tb_tile_mm.v"), os.path.join(HERE, "tile_mm.v")], check=True)
    out = subprocess.run(["vvp", "-n", os.path.join(tmp, "sim"), "+k=%d" % k, "+m=%d" % m, "+nb=%d" % nb], cwd=tmp, capture_output=True, text=True).stdout
    cyc = int([l for l in out.splitlines() if l.startswith("CYCLES")][0].split()[1]); acc = np.zeros((m, nb * lanes), np.int64); seen = 0
    for line in open(os.path.join(tmp, "out.txt")):
        r, b, h = line.split(); r, b = int(r), int(b); v = int(h, 16); seen += 1
        for l in range(lanes): x = (v >> (32 * l)) & 0xFFFFFFFF; acc[r, b * lanes + l] = x - (1 << 32) if x >> 31 else x
    return acc[:, :n], cyc, seen, m * nb
cases = []
# self-test of M1: weights and inputs exactly as the simulator saw them
st = os.path.join(W, "selftest"); sw_ = tensor(st, "w"); sb = tensor(st, "b"); sa_in = np.fromfile(os.path.join(st, "inputs.bin"), np.float32).reshape(8, 16)
cases.append(("selftest_8x16x8", sa_in, sw_, sb)); lm = os.path.join(W, "lm"); rng = np.random.RandomState(0)
cases.append(("L0.wq_64x256x256", rng.uniform(-3, 3, (64, 256)).astype(np.float32), tensor(lm, "L0.wq"), None)); cases.append(("L0.w1_16x256x1024", rng.uniform(-3, 3, (16, 256)).astype(np.float32), tensor(lm, "L0.w1"), None))
ok_all = True; sim_out = np.fromfile(os.path.join(st, "out_int8.bin"), np.float32).reshape(8, 8)
for name, a, w, bias in cases:
    qa, sa = quant_a(a); qw, sw = quant_w(w); ref = qa @ qw
    for lanes in (64, 256):
        acc, cyc, seen, nblocks_rows = run_rtl(qa, qw, lanes); m, k = qa.shape; n = qw.shape[1]; nb = math.ceil(n / lanes); exact = bool(np.array_equal(acc, ref)); expect = m * nb * k + 3; macs = m * k * n
        r = dict(case=name, lanes=lanes, accumulators_equal_numpy=exact, mismatches=int((acc != ref).sum()), outputs_seen=seen, outputs_expected=nblocks_rows, cycles=cyc, formula_m_nb_k_plus_3=expect, cycle_error_pct=100.0 * (cyc - expect) / expect, utilisation=macs / (cyc * lanes))
        if name.startswith("selftest"):
            deq = (acc.astype(np.float32) * sa * sw[None, :] + bias[None, :]).astype(np.float32); r["dequantised_equals_simulator_output"] = bool(np.array_equal(deq, sim_out)); r["max_abs_diff_vs_simulator"] = float(np.abs(deq - sim_out).max())
        res.setdefault("cases", []).append(r); ok_all &= exact and seen == nblocks_rows
# decode utilisation: one row, k = 256, n = 256, 256 lanes (a weight tensor of the M1 transformer, one real activation row)
qa, _ = quant_a(rng.uniform(-3, 3, (1, 256)).astype(np.float32)); qw, _ = quant_w(tensor(lm, "L0.wq")); acc, cyc, seen, _ = run_rtl(qa, qw, 256)
res["decode_1x256x256_lanes256"] = dict(exact=bool(np.array_equal(acc, qa @ qw)), cycles=cyc, utilisation=256 * 256 / (cyc * 256)); res["all_accumulators_exact"] = ok_all
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(HERE, "results", "m3_check.json"), "w"), indent=1)
