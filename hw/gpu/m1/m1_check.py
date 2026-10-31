#!/usr/bin/env python3
"""M1 checks (31 Oct 2026): compares the simulator outputs with the PyTorch reference and the analytic counts. usage: python m1_check.py OUTDIR  (after export_models.py and gpu_sim runs)
Bars (hw/gpu/ISA_M1.md and docs/own_gpu_charter.md, written before the work): (a) fp32 relative error <= 1e-2; (b) INT8 top-1 agreement with the PyTorch fp32 argmax >= 99% on 1,000 positions or images; (c) counted multiply-adds and SRAM bytes within 5% of the analytic model."""
import json, os, sys
import numpy as np
D = sys.argv[1]; res = {}
def rd(p, shape=None): a = np.fromfile(p, np.float32); return a if shape is None else a.reshape(shape)
# self-test of the INT8 matrix path (independent numpy W8A8 emulation) and of the fp32 path
st = os.path.join(D, "selftest"); ref8 = rd(os.path.join(st, "ref_int8.bin")); ref = rd(os.path.join(st, "ref.bin"))
res["selftest_int8_max_abs_diff_vs_numpy_w8a8"] = float(np.abs(rd(os.path.join(st, "out_int8.bin")) - ref8).max()); res["selftest_fp32_max_abs_diff_vs_numpy"] = float(np.abs(rd(os.path.join(st, "out_fp32.bin")) - ref).max())
for name in ("cnn", "lm"):
    d = os.path.join(D, name)
    if not os.path.exists(os.path.join(d, "out_int8.bin")): continue
    ref = rd(os.path.join(d, "ref.bin")); n = ref.size; r = {}
    for mode in ("fp32", "int8"):
        out = rd(os.path.join(d, "out_%s.bin" % mode)); assert out.size == ref.size, (out.size, ref.size)
        classes = 10 if name == "cnn" else 128; o2, r2 = out.reshape(-1, classes), ref.reshape(-1, classes)
        r[mode] = dict(rel_err=float(np.abs(out - ref).max() / np.abs(ref).max()), top1_agreement=float((o2.argmax(1) == r2.argmax(1)).mean()), positions=int(o2.shape[0]))
        if name == "cnn": lab = np.load(os.path.join(d, "labels.npy")); r[mode]["accuracy_vs_labels"] = float((o2.argmax(1) == lab).mean())
    r["torch_fp32_accuracy"] = float((ref.reshape(-1, 10).argmax(1) == np.load(os.path.join(d, "labels.npy"))).mean()) if name == "cnn" else None
    an = json.load(open(os.path.join(d, "analytic.json"))); cf = json.load(open(os.path.join(d, "counters_fp32.json"))); ci = json.load(open(os.path.join(d, "counters_int8.json")))
    per = {}
    for tag, v in an["per_tag"].items(): per[tag] = dict(analytic_macs=v["macs"], sim_macs=cf["per_tag"].get(tag, {}).get("macs", 0), match=abs(cf["per_tag"].get(tag, {}).get("macs", 0) - v["macs"]) <= 0.05 * max(1, v["macs"]))
    r["macs"] = dict(analytic_total=an["total_macs"], sim_total_fp32=cf["total"]["macs"], sim_total_int8=ci["total"]["macs"], per_tag=per)
    # analytic SRAM bytes (int8 configuration): weights read once per matrix operation, activations 2 bytes; written separately from the program
    if name == "cnn":
        wr = 144 * 16 + 144 * 16 * 0; mm = [(26 * 26, 9, 16), (11 * 11, 144, 32), (1, 800, 10)]
        wread = sum(k * n for _, k, n in mm)  # 1 byte per weight; activation reads counted per fetch in the simulator
        r["sram_weight_bytes_analytic"] = int(wread)
    r["counters_int8_total"] = ci["total"]; r["counters_int8_mesh_side"] = ci["mesh_side"]; res[name] = r
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(D, "m1_check.json"), "w"), indent=1)
