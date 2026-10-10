"""SPARK v2 beside real GPUs: two system modes, driven by the v2 golden model + RLCD confidence LUT.

Mode A "answer" (lossy cascade): SPARK writes a byte when its calibrated confidence >= tau; otherwise the GPU
  produces the rest of the current LLM token. GPU decode steps per token = fraction of tokens with any unconfident byte.
Mode B "draft" (lossless speculative decoding, Leviathan et al. 2023 style): SPARK drafts bytes while confidence >= tau
  (max K); the GPU verifies the draft in ONE forward pass (one weight read), keeps the longest prefix that equals its own
  greedy output (whole LLM tokens only) and adds one token of its own. Output is identical to the GPU alone.
Both are evaluated teacher-forced on the held-out test text (standard for cascade / early-exit studies).
GPU energy/time: same datasheet model as gpu_sim.py. SPARK energy: 60.8 pJ per cycle (as-built switching-activity power
simulation: 104 nJ / 1,714 cycles and 648 nJ / 10,665 cycles both give 60.8 pJ/cycle) x cycles per byte estimated from
the event counts (calibrated on RTL cycle measurements; to be replaced by v2 RTL measurements).
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "golden")); sys.path.insert(0, os.path.join(HERE, "..", "train"))
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa: E402
from gpu_sim import GPUS, MODELS, ETA_BW, ETA_C, LAUNCH, BUSY_FLOOR, CTX, PRETOK, WUE_L_PER_KWH  # noqa: E402

PJ_PER_CYCLE = 60.8e-12
F_CLK = 50e6
OUTDIM = (128, 128, 256, 256)
P_LANES = 8


def cycles(o, lanes=P_LANES):
    """Cycle estimate per byte from processed events (engine), stage scans and post-processing (RTL-calibrated)."""
    if o["path"] == 2 and sum(o["proc"]) == 0:
        return 24                                         # 4 recall tables: read, compare, back-off, LUT
    ran = [k for k in range(4) if o["proc"][k] > 0 or (k in (0, 1, 3) and o["path"] == 0) or (k in (0, 2) and o["path"] == 1)]
    eng = sum(o["proc"][k] * OUTDIM[k] / lanes for k in range(4))
    return 24 + eng + 71 * len(ran) + 80 * len(ran)


def run_spark(W, data, lut, tb=12):
    cfg = dict(recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
    g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", **cfg), tb=tb, lut=lut)
    r = [g.step(int(b)) for b in data]
    return (np.array([o["pred"] for o in r]), np.array([o["conf"] for o in r]) / 255.0,
            np.array([cycles(o) for o in r]), np.array([cycles(o, 32) for o in r]))


def token_ends(text):
    ends = np.zeros(len(text), bool)
    for m in PRETOK.finditer(text.decode("latin-1")):
        ends[m.end() - 1] = True
    return ends


def mode_a(sp, conf, gp, truth, ends, tau):
    n = len(truth) - 1
    steps = toks = right = 0
    i = 0
    while i < n:
        if conf[i] >= tau:
            right += sp[i] == truth[i + 1]
            if ends[i + 1]:
                toks += 1
            i += 1
        else:
            steps += 1
            while True:                                   # GPU writes the rest of this token
                right += gp[i] == truth[i + 1]
                i += 1
                if i >= n or ends[i]:
                    toks += 1
                    break
    return {"gpu_steps_per_token": steps / max(1, toks), "accuracy": right / n}


def mode_b(sp, conf, gp, ends, tau, K=24):
    n = len(gp) - 1
    steps = toks = drafted = 0
    i = 0
    while i < n:
        j = 0
        while j < K and i + j < n and conf[i + j] >= tau:   # SPARK drafts while confident
            j += 1
        drafted += j
        acc = 0
        while acc < j and sp[i + acc] == gp[i + acc]:
            acc += 1
        # keep whole tokens only: last token end inside the accepted bytes
        k = acc
        while k > 0 and not ends[i + k]:
            k -= 1
        new_toks = int(ends[i + 1:i + k + 1].sum()) if k > 0 else 0
        i += k
        # bonus: GPU's own next token
        while i < n:
            i += 1
            if ends[i] if i < len(ends) else True:
                break
        steps += 1
        toks += new_toks + 1
    return {"gpu_steps_per_token": steps / max(1, toks), "tokens_per_step": toks / max(1, steps),
            "draft_bytes_per_step": drafted / max(1, steps)}


def gpu_energy(g, m, steps_per_token, batch, extra_flops_frac=0.0, mode="draft"):
    """Energy and time per token for a GPU serving `batch` users.
    draft : every pass serves all users and advances each by 1/steps_per_token tokens (weights read once per pass).
    answer: users advance one token per time slot; in each slot only a fraction steps_per_token of them need the GPU,
            and a pass is needed if any of them does (weights read once per pass, KV/compute only for active users)."""
    w = m["P"] * 2
    kv_r = 2 * m["L"] * m["kv"] * CTX * 2
    if mode == "draft":
        tok_per_step = 1.0 / steps_per_token
        flops = batch * tok_per_step * (1 + extra_flops_frac) * 2 * m["P"]
        bytes_ = w + batch * kv_r
        toks = batch * tok_per_step
        p_need = 1.0
    else:
        k = batch * steps_per_token                       # users needing the GPU per slot (expected)
        p_need = 1 - (1 - steps_per_token) ** batch       # probability a pass is needed in a slot
        flops = k / p_need * 2 * m["P"]
        bytes_ = w + k / p_need * kv_r
        toks = batch / p_need                             # tokens delivered per GPU pass
    dt = max(bytes_ / (g["bw"] * ETA_BW), flops / (g["peak"] * ETA_C)) + LAUNCH
    p = min(g["tdp"], g["idle"] + BUSY_FLOOR * g["tdp"] + (bytes_ * 8 * g["e_bit"] + flops * g["e_flop"]) / dt)
    return p * dt / toks, toks / dt


def main():
    data = tr.load_corpus(3_000_000); n = len(data)
    test = data[int(n * 0.95): int(n * 0.95) + 20000]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    rl = json.load(open(os.path.join(HERE, "..", "rlcd", "out", "rlcd_results.json")))
    lut = rl["lut_rlcd_8bit"]
    import torch
    from cascade_sim import gpu_preds, GPT, GPTConfig
    ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); gm = GPT(GPTConfig(**ck["cfg"])); gm.load_state_dict(ck["state"]); gm.eval()
    gp = gpu_preds(gm, test)
    sp, conf, cyc8, cyc32 = run_spark(W, test, lut)
    ends = token_ends(bytes(test))
    bpt = len(test) / ends.sum()
    gpu_acc = float(np.mean(gp[:-1] == test[1:]))
    spark_j_byte = float(np.mean(cyc8) * PJ_PER_CYCLE)
    out = {"gpu_model_accuracy": gpu_acc, "spark_accuracy": float(np.mean(sp[:-1] == test[1:])),
           "spark_cycles_per_byte": {"8 lanes": float(np.mean(cyc8)), "32 lanes": float(np.mean(cyc32))},
           "spark_nJ_per_byte": spark_j_byte * 1e9, "bytes_per_token": float(bpt), "points": []}
    print(f"GPU model (nanoGPT, {sum(p.numel() for p in gm.parameters())/1e6:.1f} M) accuracy {gpu_acc:.1%}; SPARK v2 accuracy {out['spark_accuracy']:.1%}")
    print(f"SPARK v2: {np.mean(cyc8):.0f} cycles/byte (8 lanes), {np.mean(cyc32):.0f} (32 lanes); {spark_j_byte*1e9:.1f} nJ/byte")
    for tau in (0.6, 0.7, 0.8, 0.9, 0.95):
        A = mode_a(sp, conf, gp, test, ends, tau)
        B = mode_b(sp, conf, gp, ends, tau)
        pt = {"tau": tau, "A": A, "B": B, "energy": []}
        print(f"\ntau {tau}: A answer-mode: GPU steps/token {A['gpu_steps_per_token']:.3f}, accuracy {A['accuracy']:.1%} (GPU alone {gpu_acc:.1%}) | "
              f"B draft-mode (lossless): GPU steps/token {B['gpu_steps_per_token']:.3f} ({B['tokens_per_step']:.2f} tokens per GPU pass)")
        for gname in ("H100 SXM", "RTX 4090", "L4"):
            for mname in ("7B", "13B"):
                for Bt in (1, 8, 32):
                    g, m = GPUS[gname], MODELS[mname]
                    e0, r0 = gpu_energy(g, m, 1.0, Bt)
                    eA, rA = gpu_energy(g, m, A["gpu_steps_per_token"], Bt, mode="answer")
                    eB, rB = gpu_energy(g, m, B["gpu_steps_per_token"], Bt, extra_flops_frac=B["draft_bytes_per_step"] / bpt * B["gpu_steps_per_token"])
                    sj = bpt * spark_j_byte
                    row = {"gpu": gname, "model": mname, "batch": Bt, "gpu_only_mJ": e0 * 1e3,
                           "A_mJ": (eA + sj) * 1e3, "B_mJ": (eB + sj) * 1e3,
                           "A_saving_x": e0 / (eA + sj), "B_saving_x": e0 / (eB + sj),
                           "tok_s_gpu_only": r0, "tok_s_B": rB}
                    pt["energy"].append(row)
                    if mname == "7B":
                        print(f"   {gname:9s} {mname:4s} B={Bt:2d}: GPU-only {e0*1e3:8.1f} mJ/tok | A {row['A_mJ']:8.1f} ({row['A_saving_x']:.2f}x) | B lossless {row['B_mJ']:8.1f} ({row['B_saving_x']:.2f}x, {r0:.0f}->{rB:.0f} tok/s)")
        out["points"].append(pt)
    json.dump(out, open(os.path.join(HERE, "out", "spark_v2_system.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
