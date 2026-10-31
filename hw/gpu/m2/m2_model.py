#!/usr/bin/env python3
"""M2 analytic model (31 Oct 2026): per-token counts, cycles and energy of a dense decoder from its dimensions, with the simulator's rules and constants (hw/gpu/M2_plan.md).
Validates against the simulator on the small transformer decoded for 64 steps (bars M2-a, M2-b) and evaluates a dense 1B decoder at batch 1 and 64 against the step 5 model (bars M2-d, M2-e).
usage: python m2_model.py WORKDIR   (WORKDIR from export_models.py/export_decode.py with the simulator run in decode mode; /tmp/s5 = built step5_worst_case_model.rs)"""
import json, math, os, subprocess, sys
# ASSUMED constants, identical to gpu_sim.rs
MACPC, SRAMBW, VECL, HOPCYC = 368.0, 2000.0, 64.0, 2
E_SRAM_BYTE, E_VEC, E_HOP_BYTE, LEAK_W_PER_TILE = 0.55 * 8, 0.4, 0.1 * 8, 1.6 * (4 * 1024 * 1024 / 2 ** 30)
CLOCK = 1e9

def step_ops(NL, d, ff, heads, V, t, B, wb, a, kvb, kvd=None):
    """list of (tag, macs, rd, wr, vec) for one decode step of B sequences at context length t (the cache holds t entries after the append)."""
    kvd = kvd or d; ops = []; add = lambda tag, macs=0, rd=0, wr=0, vec=0: ops.append((tag, macs, rd, wr, vec))
    add("emb", 0, B * a + B * d * wb, B * d * a); add("emb", 0, B * a + B * d * wb, B * d * a); add("emb", 0, 2 * B * d * a, B * d * a, B * d)
    ln = lambda tag: add(tag, 0, B * d * a, B * d * a, 4 * B * d)
    mm = lambda tag, k, n: add(tag, B * k * n, B * k * a + k * n * wb, B * n * a, B * n)
    for l in range(NL):
        g = "L%d." % l; ln(g + "attn")
        for _ in range(3): mm(g + "attn", d, d)
        add(g + "attn", 0, B * d * a, B * kvd * kvb); add(g + "attn", 0, B * d * a, B * kvd * kvb)
        add(g + "attn", 2 * B * d * t, B * d * a + 2 * B * t * kvd * kvb, B * d * a, 3 * B * heads * t)
        mm(g + "attn", d, d); add(g + "attn", 0, 2 * B * d * a, B * d * a, B * d)
        ln(g + "mlp"); mm(g + "mlp", d, ff); add(g + "mlp", 0, B * ff * a, B * ff * a, B * ff); mm(g + "mlp", ff, d); add(g + "mlp", 0, 2 * B * d * a, B * d * a, B * d)
    ln("head"); mm("head", d, V); return ops

def cost(ops, R=1, fabric_phases_per_layer=0, NL=0, side=1, B=1, d=1, a=2):
    """cycles and dynamic energy of a step; R tiles share every operation; a mesh reduction of fabric_phases_per_layer phases per layer adds cycles and mesh energy."""
    cyc, en, per = 0.0, 0.0, {}
    for tag, macs, rd, wr, vec in ops:
        c = math.ceil(max(macs / (R * MACPC), (rd + wr) / (R * SRAMBW), vec / (R * VECL))); e = macs * EMAC + (rd + wr) * E_SRAM_BYTE + vec * E_VEC
        cyc += c; en += e; p = per.setdefault(tag, dict(macs=0, rd=0, wr=0, cycles=0)); p["macs"] += macs; p["rd"] += rd; p["wr"] += wr; p["cycles"] += c
    if fabric_phases_per_layer:
        hops = 2 * math.ceil(math.sqrt(R)); fc = NL * fabric_phases_per_layer * hops * HOPCYC; cyc += fc; en += NL * fabric_phases_per_layer * B * d * a * hops * E_HOP_BYTE
    return cyc, en, per

res = {}; W = sys.argv[1]
# ---- validation on the small transformer (2 layers, d 256, ff 1024, 4 heads, vocabulary 128), 64 decode steps, int8 configuration, one tile per operation
EMAC = 0.25; tot_cyc = 0.0; tot = {}
for t in range(1, 65):
    c, e, per = cost(step_ops(2, 256, 1024, 4, 128, t, 1, 1, 2, 2), R=1); tot_cyc += c
    for tag, p in per.items(): q = tot.setdefault(tag, dict(macs=0, rd=0, wr=0, cycles=0)); [q.__setitem__(k, q[k] + p[k]) for k in p]
sim = json.load(open(os.path.join(W, "lm_dec", "counters_int8.json"))); rows = {}
for tag, p in tot.items():
    s = sim["per_tag"][tag]; rel = lambda x, y: abs(x - y) / max(1, y)
    rows[tag] = dict(macs=(p["macs"], s["macs"]), read=(p["rd"], s["sram_read_bytes"]), write=(p["wr"], s["sram_write_bytes"]), cycles=(p["cycles"], s["cycles"]),
                     ok_counts=bool(rel(p["macs"], s["macs"]) <= 0.05 and rel(p["rd"], s["sram_read_bytes"]) <= 0.05 and rel(p["wr"], s["sram_write_bytes"]) <= 0.05))
res["validation"] = dict(per_tag=rows, counts_within_5pct=all(r["ok_counts"] for r in rows.values()), cycles_analytic_per_token=tot_cyc / 64, cycles_simulator_per_token=sim["total"]["cycles"] / 64, cycles_ratio=(tot_cyc / 64) / (sim["total"]["cycles"] / 64))
res["validation"]["cycles_within_20pct"] = abs(res["validation"]["cycles_ratio"] - 1) <= 0.20
# decode equals full pass (bar M2-c)
import numpy as np
full = np.fromfile(os.path.join(W, "lm", "out_fp32.bin"), np.float32).reshape(16, 64, 128)[0]; dec = np.fromfile(os.path.join(W, "lm_dec", "out_fp32.bin"), np.float32).reshape(64, 128)
res["decode_vs_full_pass_relative_error"] = float(np.abs(dec - full).max() / np.abs(full).max())
# ---- dense 1B decoder: 16 layers, d 2048, ff 8192, 16 heads, vocabulary 32,000, context 2,048, 4-bit weights, 16-bit cache; all tiles of the system share every operation
EMAC = 0.12; NL, d, ff, H, V, ctx = 16, 2048, 8192, 16, 32000, 2048; params = NL * (4 * d * d + 2 * d * ff) + d * V; res["one_b_parameters_read_per_token"] = params; ref = {}
for B in (1, 64):
    wbytes = params * 0.5; kv = B * 2 * NL * d * ctx * 2; tiles = math.ceil((wbytes + kv) / (4 * 1024 * 1024)); R = tiles
    cyc, dyn, per = cost(step_ops(NL, d, ff, H, V, ctx, B, 0.5, 2, 2), R=R, fabric_phases_per_layer=6, NL=NL, B=B, d=d, a=2); t_s = cyc / CLOCK; static = tiles * LEAK_W_PER_TILE * t_s * 1e12
    out = subprocess.run(["/tmp/s5"], env=dict(os.environ, MODEL_TOTAL="1e9", MODEL_LAYERS=str(NL), MODEL_D=str(d), MODEL_KVDIV="1", CTX=str(ctx), FIXED_B=str(B), SRAM_PJ="0.55", MM2GB="420", LEAK="1.6", W_BITS="4", KV_BITS="16"), capture_output=True, text=True).stdout
    r5 = dict(x.split() for x in out.replace("M2REF ", "").split(" ")[0:0]) if False else None; toks = out.split(); j5 = float(toks[toks.index("j_per_token") + 1]); lat5 = float(toks[toks.index("latency_s") + 1]); ch5 = int(toks[toks.index("chips") + 1])
    ej = (dyn + static) * 1e-12 / B; res["one_b_batch%d" % B] = dict(tiles=tiles, chips_equivalent=tiles * 4 * 1024 * 1024 / (1.88e9), cycles_per_step=cyc, step_time_s=t_s, energy_per_token_J=ej, dynamic_J_per_token=dyn * 1e-12 / B, static_J_per_token=static * 1e-12 / B,
        step5_energy_per_token_J=j5, step5_latency_s=lat5, step5_chips=ch5, energy_ratio=ej / j5, latency_ratio=t_s / lat5, energy_within_20pct=abs(ej / j5 - 1) <= 0.2, latency_within_20pct=abs(t_s / lat5 - 1) <= 0.2)
# ---- informational cross-check, not a bar: the same model on the two Llama-3.1-class dense models for which a vendor reported per-user speeds on wafer-scale hardware (16-bit weights, batch 1, short context, grouped-query cache)
EMAC = 1.5
for name, NL2, d2, ff2, H2, V2, kvd2, vendor in (("70B", 80, 8192, 28672, 64, 128256, 1024, 2100), ("405B", 126, 16384, 53248, 128, 128256, 1024, 969)):
    prm = NL2 * (2 * d2 * d2 + 2 * d2 * kvd2 + 2 * d2 * ff2 * 1.5) + d2 * V2; tiles = math.ceil((prm * 2) / (4 * 1024 * 1024)); cyc, dyn, per = cost(step_ops(NL2, d2, ff2, H2, V2, 1024, 1, 2, 2, 2, kvd2), R=tiles, fabric_phases_per_layer=6, NL=NL2, B=1, d=d2, a=2)
    res["crosscheck_" + name] = dict(tiles=tiles, tokens_per_s_model=CLOCK / cyc, vendor_reported_tokens_per_s=vendor, ratio_model_to_vendor=(CLOCK / cyc) / vendor)
print(json.dumps(res, indent=1)); json.dump(res, open(os.path.join(W, "m2_model.json"), "w"), indent=1)
