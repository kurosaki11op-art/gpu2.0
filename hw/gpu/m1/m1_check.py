#!/usr/bin/env python3
"""M1 checks (31 Oct 2026): compares the simulator outputs with the PyTorch reference and with analytic counts derived from the model dimensions (not from the program text).
usage: python m1_check.py OUTDIR  (after export_models.py and gpu_sim runs in modes fp32, w8, int8)
Bars (docs/own_gpu_charter.md, written before the work): (a) fp32 relative error <= 1e-2; (b) with INT8 weights, top-1 agreement with the PyTorch fp32 argmax >= 99% on 1,000 positions or images;
(c) counted multiply-adds and SRAM bytes per layer within 5% of the analytic model. Modes: fp32 (reference), w8 (INT8 weights, FP32 activations), int8 (W8A8, the ISA configuration)."""
import json, os, sys
import numpy as np
D = sys.argv[1]; res = {}; AB, WB = 2, 1   # bytes: activations 2, weights 1 in the INT8 configurations
def rd(p): return np.fromfile(p, np.float32)

def analytic_cnn():
    """per tag (rd, wr) bytes for one image, int8 configuration. Rules: every operand tensor read once by the operation that consumes it (activations 2 B, weights 1 B), every result written once (2 B)."""
    a = {"load": dict(rd=0, wr=144 * 16 // 16 * 1), "conv1": {}, "conv2": {}, "fc": {}}
    a["load"] = dict(rd=0, wr=9 * 16 + 144 * 32 + 800 * 10)
    c1o, p1o, c2o, p2o = 16 * 26 * 26, 16 * 13 * 13, 32 * 11 * 11, 32 * 5 * 5
    a["conv1"] = dict(rd=AB * 28 * 28 + 9 * 16 + AB * c1o + AB * c1o, wr=AB * c1o + AB * c1o + AB * p1o)
    a["conv2"] = dict(rd=AB * p1o + 144 * 32 + AB * c2o + AB * c2o, wr=AB * c2o + AB * c2o + AB * p2o)
    a["fc"] = dict(rd=AB * 800 + 800 * 10, wr=AB * 10); return a

def analytic_lm(T=64, d=256, ff=1024, V=128, NL=2):
    td, tf = T * d * AB, T * ff * AB; a = {}
    a["load"] = dict(rd=0, wr=V * d + T * d + NL * (4 * d * d + 2 * d * ff) + d * V)
    a["emb"] = dict(rd=2 * T * AB + 2 * T * d * WB + 2 * td, wr=3 * td)
    for l in range(NL):
        attn_rd = td + 3 * (td + d * d * WB) + 3 * td + (td + d * d * WB) + 2 * td; attn_wr = td + 3 * td + td + td + td
        mlp_rd = td + (td + d * ff * WB) + tf + (tf + ff * d * WB) + 2 * td; mlp_wr = td + tf + tf + td + td
        a["L%d.attn" % l] = dict(rd=attn_rd, wr=attn_wr); a["L%d.mlp" % l] = dict(rd=mlp_rd, wr=mlp_wr)
    a["head"] = dict(rd=td + td + d * V * WB, wr=td + T * V * AB); return a

# self-test of the INT8 matrix path (independent numpy W8A8 emulation) and of the fp32 path
st = os.path.join(D, "selftest"); res["selftest_int8_max_abs_diff_vs_numpy_w8a8"] = float(np.abs(rd(os.path.join(st, "out_int8.bin")) - rd(os.path.join(st, "ref_int8.bin"))).max())
res["selftest_fp32_max_abs_diff_vs_numpy"] = float(np.abs(rd(os.path.join(st, "out_fp32.bin")) - rd(os.path.join(st, "ref.bin"))).max())
for name in ("cnn", "lm"):
    d = os.path.join(D, name); ref = rd(os.path.join(d, "ref.bin")); classes = 10 if name == "cnn" else 128; r = {}
    for mode in ("fp32", "w8", "int8"):
        out = rd(os.path.join(d, "out_%s.bin" % mode)); assert out.size == ref.size; o2, r2 = out.reshape(-1, classes), ref.reshape(-1, classes)
        r[mode] = dict(rel_err=float(np.abs(out - ref).max() / np.abs(ref).max()), top1_agreement=float((o2.argmax(1) == r2.argmax(1)).mean()), positions=int(o2.shape[0]))
        if name == "cnn": lab = np.load(os.path.join(d, "labels.npy")); r[mode]["accuracy_vs_labels"] = float((o2.argmax(1) == lab).mean())
    an = json.load(open(os.path.join(d, "analytic.json"))); cf = json.load(open(os.path.join(d, "counters_fp32.json"))); ci = json.load(open(os.path.join(d, "counters_int8.json"))); cw = json.load(open(os.path.join(d, "counters_w8.json")))
    per = {}
    for tag, v in an["per_tag"].items(): s = cf["per_tag"].get(tag, {}).get("macs", 0); per[tag] = dict(analytic=v["macs"], simulator=s, within_5pct=abs(s - v["macs"]) <= 0.05 * max(1, v["macs"]))
    r["macs"] = dict(analytic_total=an["total_macs"], simulator_total=ci["total"]["macs"], per_tag=per, all_within_5pct=all(v["within_5pct"] for v in per.values()))
    ab = analytic_cnn() if name == "cnn" else analytic_lm(); sb = {}
    for tag, v in ab.items():
        s = ci["per_tag"].get(tag, {}); sb[tag] = dict(analytic_read=v["rd"], simulator_read=s.get("sram_read_bytes", 0), analytic_write=v["wr"], simulator_write=s.get("sram_write_bytes", 0),
                                                       within_5pct=abs(s.get("sram_read_bytes", 0) - v["rd"]) <= 0.05 * max(1, v["rd"]) and abs(s.get("sram_write_bytes", 0) - v["wr"]) <= 0.05 * max(1, v["wr"]))
    r["sram_bytes_per_sample_int8"] = dict(per_tag=sb, all_within_5pct=all(v["within_5pct"] for v in sb.values())); r["w8_counters_equal_int8"] = cw["total"] == ci["total"]
    r["counters_int8_total"] = ci["total"]; r["mesh_side"] = ci["mesh_side"]; res[name] = r
if "lm" in res:
    ref = rd(os.path.join(D, "lm", "ref.bin")).reshape(-1, 128); o = rd(os.path.join(D, "lm", "out_int8.bin")).reshape(-1, 128); s = np.sort(ref, 1); gap = s[:, -1] - s[:, -2]; dis = o.argmax(1) != ref.argmax(1)
    res["lm_int8_disagreements"] = dict(count=int(dis.sum()), of=int(len(dis)), median_fp32_top1_top2_gap_at_disagreements=float(np.median(gap[dis])) if dis.any() else None, max_gap_at_disagreements=float(gap[dis].max()) if dis.any() else None, median_gap_all=float(np.median(gap)))
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(D, "m1_check.json"), "w"), indent=1)
