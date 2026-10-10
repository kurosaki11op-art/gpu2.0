"""Software GPU testbench: SPARK beside real GPUs, driven by datasheet numbers and our real token stream.

Token by token, on the held-out test text:
  * SPARK (bit-exact golden model of the verified chip) runs on every byte; its `path` pin says whether it is
    confident (path 1/2) or not (path 0).
  * The GPU serves an LLM decode stream. An LLM token (approx. BPE: GPT-2-style pre-tokenizer pieces) needs a
    GPU decode step unless SPARK was confident on every byte of it. Skipped tokens are absorbed into the next GPU
    step as prefill: their FLOPs and KV-cache writes are still paid, only the weight read is avoided.
  * GPU step time = max(bytes / (BW * eta_bw), flops / (peak * eta_c)) + launch overhead
    GPU power     = idle while waiting; when busy: idle + busy floor (fraction of TDP) + dynamic
                    (bytes * e_mem + flops * e_flop) / step time, capped at TDP.
  * Batch B: B independent users (different positions in the stream) share each step's weight read; a step is
    needed when any of them needs the GPU.
Datasheet: memory bandwidth, peak dense FP16 tensor FLOP/s, TDP. ESTIMATES: idle power, pJ/bit, pJ/FLOP,
efficiencies, busy floor, KV length. SPARK: 104 nJ/byte (switching-activity power sim, upper end of low effort),
4,190 cycles/byte at 50 MHz (RTL sim). Water: 1.8 L/kWh data-centre water-usage effectiveness (ESTIMATE).
"""
import json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "train"))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as sg      # noqa: E402
import train_spark_v0 as tr    # noqa: E402

GPUS = {
    "H100 SXM":  dict(bw=3.35e12, peak=989e12, tdp=700, idle=70, e_bit=3.9e-12, e_flop=0.35e-12),
    "A100 SXM":  dict(bw=2.039e12, peak=312e12, tdp=400, idle=50, e_bit=3.9e-12, e_flop=0.5e-12),
    "RTX 4090":  dict(bw=1.008e12, peak=165e12, tdp=450, idle=20, e_bit=7.25e-12, e_flop=0.5e-12),
    "L4":        dict(bw=0.300e12, peak=121e12, tdp=72, idle=16, e_bit=7.5e-12, e_flop=0.5e-12),
}
MODELS = {   # params, layers, KV width (kv_heads * head_dim)
    "1.1B": dict(P=1.1e9, L=24, kv=2048),
    "7B":   dict(P=6.7e9, L=32, kv=4096),
    "13B":  dict(P=13.0e9, L=40, kv=5120),
}
ETA_BW, ETA_C, LAUNCH, BUSY_FLOOR, CTX = 0.80, 0.50, 20e-6, 0.35, 1024
SPARK_J_PER_BYTE, SPARK_S_PER_BYTE = 104e-9, 4190 / 50e6
WUE_L_PER_KWH = 1.8
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
SETTINGS = {
    "safe":       dict(recall=1, conf_th=1, recall_mode=0, exit_en=1, exit_th=64),
    "balanced":   dict(recall=1, conf_th=1, recall_mode=0, exit_en=1, exit_th=32),
    "aggressive": dict(recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16),
}


def token_needs_gpu(text, paths):
    s = text.decode("latin-1")
    need = [bool(np.any(paths[a:b] == 0)) for a, b in (m.span() for m in PRETOK.finditer(s))]
    return np.array(need), len(s) / max(1, len(need))


def simulate(g, m, need, batch, bpt, use_spark):
    n = len(need)
    w_bytes, flops_tok = m["P"] * 2, 2 * m["P"]
    kv_read, kv_write = 2 * m["L"] * m["kv"] * CTX * 2, 2 * m["L"] * m["kv"] * 2
    offs = np.random.default_rng(0).integers(0, n, size=batch)
    E = T = 0.0
    steps, pending = 0, np.zeros(batch)
    for t in range(n):
        nd = need[(offs + t) % n] if use_spark else np.ones(batch, bool)
        if use_spark:
            ts = bpt * SPARK_S_PER_BYTE
            E += batch * bpt * SPARK_J_PER_BYTE + g["idle"] * ts
            T += ts
        k = int(nd.sum())
        pending[~nd] += 1
        if k == 0:
            continue
        catch = float(pending[nd].sum()); pending[nd] = 0
        b = w_bytes + k * kv_read + (k + catch) * kv_write
        f = (k + catch) * flops_tok
        dt = max(b / (g["bw"] * ETA_BW), f / (g["peak"] * ETA_C)) + LAUNCH
        p = min(g["tdp"], g["idle"] + BUSY_FLOOR * g["tdp"] + (b * 8 * g["e_bit"] + f * g["e_flop"]) / dt)
        E += p * dt; T += dt; steps += 1
    return {"J_per_token": E / (n * batch), "tokens_per_s": n * batch / T, "gpu_steps_frac": steps / n,
            "avg_power_W": E / T}


def main():
    data = tr.load_corpus(3_000_000); n = len(data)
    test = data[int(n * 0.95): int(n * 0.95) + 20000]
    W = sg.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    out = {"assumptions": {"ETA_BW": ETA_BW, "ETA_C": ETA_C, "LAUNCH_s": LAUNCH, "BUSY_FLOOR": BUSY_FLOOR, "CTX": CTX,
                           "SPARK_J_per_byte": SPARK_J_PER_BYTE, "SPARK_s_per_byte": SPARK_S_PER_BYTE,
                           "WUE_L_per_kWh": WUE_L_PER_KWH, "gpus": GPUS, "models": MODELS}, "settings": {}}
    for sname, ov in SETTINGS.items():
        gl = sg.Golden(W, sg.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", **ov))
        paths = np.array([gl.step(int(b))["path"] for b in test])
        need, bpt = token_needs_gpu(bytes(test), paths)
        S = out["settings"][sname] = {"byte_offload": float((paths != 0).mean()), "token_offload": float(1 - need.mean()),
                                      "bytes_per_token": bpt, "results": []}
        print(f"\n== SPARK {sname}: answers {S['byte_offload']:.1%} of bytes -> skips GPU on {S['token_offload']:.1%} of LLM tokens ({bpt:.2f} bytes/token)")
        print(f"   {'GPU':9s} {'model':5s} {'batch':>5s} {'GPU-only mJ/tok':>16s} {'SPARK+GPU':>10s} {'saving':>7s} {'tok/s before->after':>22s} {'water mL/1k tok':>18s}")
        for gname, g in GPUS.items():
            for mname, m in MODELS.items():
                for B in (1, 8, 32):
                    a = simulate(g, m, need, B, bpt, False); s = simulate(g, m, need, B, bpt, True)
                    w = lambda r: r["J_per_token"] * 1000 / 3.6e6 * WUE_L_PER_KWH * 1000  # noqa: E731
                    row = {"gpu": gname, "model": mname, "batch": B, "gpu_only": a, "spark_gpu": s,
                           "energy_saving_x": a["J_per_token"] / s["J_per_token"],
                           "throughput_x": s["tokens_per_s"] / a["tokens_per_s"],
                           "water_mL_per_1k_gpu_only": w(a), "water_mL_per_1k_spark": w(s)}
                    S["results"].append(row)
                    print(f"   {gname:9s} {mname:5s} {B:5d} {a['J_per_token']*1e3:16.2f} {s['J_per_token']*1e3:10.2f} "
                          f"{row['energy_saving_x']:6.2f}x {a['tokens_per_s']:10.0f}->{s['tokens_per_s']:<10.0f} {w(a):8.3f}->{w(s):.3f}")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "out", "gpu_sim_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
