"""Draft mode, round 4: attack SPARK's own limits and the report's decode limits together.

SPARK limits addressed
  L1 slow network path (~2,000 cycles/byte) -> "fast draft": draft only while the recall memory answers (~6 cycles/byte)
  L2 fixed draft length wastes GPU work on rejected drafts -> confidence-chosen draft length (calibrated table in the LUT)
  L3 one chip, many users -> count how many SPARK chips a GPU needs at each batch size
  L4 must beat the free software baseline (host prompt-lookup / n-gram copy) -> report SPARK's gain over it, not over nothing
Report limits addressed: H014/H020 (decode underuse, bandwidth), H075 (throughput vs latency), section 13 exp. #3
(draft length chosen from observed bottleneck, rejected work counted, compared to the best fixed setting).

Protocol: GPU stand-in = byte-level nanoGPT (out_big), greedy, lossless verification; tokens = GPT-2-style word pieces.
Calibration on the first half of the points, everything reported on the second half (no tuning on test).
Pass cost = datasheet roofline for a 9B model (SIMULATED); acceptance = measured on the stand-in model."""
import copy, json, os, re, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
from model import GPT, GPTConfig  # noqa
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
NPTS = int(os.environ.get("NPTS", 400)); L = 40; KMAX = 8
CYC_RECALL, CYC_NET, FCLK = 6, 2000, 50e6          # cycles/byte: recall hit (RTL S_RU_RD..S_RL_DEC), network (sim avg)


def pieces(b):
    return [x.group(0).encode("latin-1") for x in PRETOK.finditer(b.decode("latin-1"))]


def match_len(dp, gp):
    m = 0
    for a, b in zip(dp, gp):
        if a != b:
            break
        m += 1
    return m


# ---------------------------------------------------------------- collect drafts and GPU truth
def collect():
    Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
    text = bytes(Z["test_text"]); s = text.decode("latin-1")
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
    ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()

    def gpu_cont(i):
        seq = list(text[max(0, i - 127):i + 1])
        with torch.no_grad():
            for _ in range(L):
                lg, _ = m(torch.tensor(seq[-128:])[None]); seq.append(int(lg[0, -1].argmax()))
        return bytes(seq[-L:])

    def copy_longest(i, nmax=32, nmin=3):
        for N in range(nmax, nmin - 1, -1):
            j = text.rfind(text[i - N + 1:i + 1], 0, i)
            if j >= 0:
                return text[j + N:j + N + L], N
        return b"", 0

    ends = sorted(x.end() - 1 for x in PRETOK.finditer(s))
    cand = [e for e in ends if 1500 <= e < len(text) - 60]
    pts = set(cand[int(k)] for k in np.linspace(0, len(cand) - 1, NPTS))
    if os.environ.get("POLICY") == "hyst":                 # recall write-back with hysteresis (recall_policy.py)
        import recall_policy
        g = recall_policy.Policy(W, cfg, tb=12, lut=lut, update="hyst")
    else:
        g = g2.GoldenV2(W, cfg, tb=12, lut=lut)
    rows, ingest = [], []
    for i, b in enumerate(text):
        o = g.step(int(b)); ingest.append(o["path"])
        if i not in pts:
            continue
        gp = pieces(gpu_cont(i))[:-1]                       # drop the possibly-cut last piece
        h = copy.deepcopy(g); d, cf, pa = [o["pred"]], [o["conf"]], [o["path"]]
        for _ in range(L - 1):
            r = h.step(int(d[-1])); d.append(r["pred"]); cf.append(r["conf"]); pa.append(r["path"])
        full, fast = bytes(d), bytes(d[:next((k for k in range(L) if pa[k] != 2), L)])   # fast: recall answers only, no network
        cpy, N = copy_longest(i)
        row = {"gp": gp, "N": N}
        for name, dr in (("full", full), ("fast", fast), ("copy", cpy)):
            dp = pieces(dr)
            if name != "copy" or len(dr) == L:
                dp = dp[:-1]                                # last piece may be cut by the draft length
            dp = dp[:KMAX]
            feats, pos = [], 0
            for x in dp:                                    # per-token confidence = product of byte confidences
                c = float(np.prod([cf[pos + q] / 255.0 for q in range(len(x))])) if name != "copy" else 0.0
                feats.append(c); pos += len(x)
            row[name] = {"k": len(dp), "m": match_len(dp, gp), "conf": feats,
                         "cyc": sum(CYC_RECALL if p == 2 else CYC_NET for p in pa[:len(dr)]) if name != "copy" else 0,
                         "bytes": len(dr)}
        rows.append(row)
    ing = np.array(ingest)
    return rows, float(np.mean(np.where(ing == 2, CYC_RECALL, CYC_NET))), float(np.mean(ing == 2))


# ---------------------------------------------------------------- calibrated per-token survival tables
def cbucket(c):
    return min(7, int(c * 8))


def nbucket(N):
    return 0 if N < 4 else 1 if N < 6 else 2 if N < 10 else 3 if N < 16 else 4


def fit_tables(rows):
    """P(token j accepted | tokens < j accepted, feature). This is what would be written into SPARK's LUT."""
    T = {k: np.tile([0.5, 1.0], (KMAX, n, 1)) for k, n in (("full", 8), ("fast", 8), ("copy", 5))}   # prior 0.5 for unseen buckets
    for r in rows:
        for name in T:
            d = r[name]
            for j in range(min(d["k"], d["m"] + 1)):
                f = nbucket(r["N"]) if name == "copy" else cbucket(d["conf"][j])
                T[name][j, f, 1] += 1; T[name][j, f, 0] += int(j < d["m"])
    return {k: v[..., 0] / v[..., 1] for k, v in T.items()}


def surv(r, name, T):
    d = r[name]
    p = [T[name][j, nbucket(r["N"]) if name == "copy" else cbucket(d["conf"][j])] for j in range(d["k"])]
    return np.cumprod(p)                                     # P(first j+1 draft tokens all accepted)


# ---------------------------------------------------------------- GPU pass cost (datasheet roofline)
GPUS = {"RTX 4090": dict(bw=1.008e12, peak=165e12), "H100 SXM": dict(bw=3.35e12, peak=989e12)}
MODEL = dict(P=9e9, L=36, kv=1024, ctx=2048)                 # 9B-class, grouped KV heads, fp16 weights + KV
ETA_BW, ETA_C, LAUNCH = 0.8, 0.5, 20e-6


def pass_time(g, B, ktot):
    """B streams, ktot extra draft tokens in total (rejected ones included) verified in one pass."""
    wb = MODEL["P"] * 2 + B * 2 * MODEL["L"] * MODEL["kv"] * MODEL["ctx"] * 2
    fl = 2 * MODEL["P"] * (B + ktot)
    return max(wb / (g["bw"] * ETA_BW), fl / (g["peak"] * ETA_C)) + LAUNCH


def policy(rows, T, how, k=0, lam=0.0):
    """returns per-row (accepted tokens incl. the bonus token, draft tokens verified, SPARK cycles)."""
    out = []
    for r in rows:
        branches = []
        for name in how:
            d = r[name]
            if d["k"] == 0:
                continue
            if k:                                             # fixed length
                kk = min(k, d["k"])
            else:                                             # confidence-chosen length: maximise E[acc] - lam*k
                sv = surv(r, name, T)
                gain = np.concatenate([[0], np.cumsum(sv)]) - lam * np.arange(d["k"] + 1)
                kk = int(gain.argmax())
            if kk:
                branches.append((min(kk, d["m"]) + 1, kk, d["cyc"] * kk / max(1, d["k"]) if name != "copy" else 0))
        if not branches:
            out.append((1, 0, 0)); continue
        out.append((max(b[0] for b in branches), sum(b[1] for b in branches), sum(b[2] for b in branches)))
    return np.array(out, float)


def speed(res, g, B, ingest_cyc, bpt, chips):
    acc, kt, cyc = res[:, 0].mean(), res[:, 1].mean(), res[:, 2].mean()
    t = pass_time(g, B, B * kt)
    # SPARK work per pass for B streams: ingest the accepted bytes + drafting; spread over `chips` chips, not overlapped
    t_spark = B * (acc * bpt * ingest_cyc + cyc) / FCLK / chips
    return acc / (t + t_spark) * pass_time(g, B, 0), acc, kt, t_spark / t


def main():
    rows, ingest_cyc, recall_frac = collect()
    half = len(rows) // 2; cal, test = rows[:half], rows[half:]
    T = fit_tables(cal)
    bpt = 4.0
    print(f"{len(rows)} points ({half} calibration / {len(test)} test). SPARK ingest: recall answers {recall_frac:.0%} of bytes, "
          f"avg {ingest_cyc:.0f} cycles/byte")
    out = {"points": len(rows), "ingest_cycles_per_byte": ingest_cyc, "recall_frac": recall_frac, "results": {}}
    print("\nAcceptance on test points (tokens per pass, unlimited GPU compute):")
    for name, how in (("copy (software baseline)", ["copy"]), ("SPARK full", ["full"]), ("SPARK fast", ["fast"]),
                      ("copy + SPARK fast", ["copy", "fast"]), ("copy + SPARK full", ["copy", "full"])):
        r = policy(test, T, how, k=KMAX)
        print(f"  {name:26s} {r[:,0].mean():.2f} tokens/pass, {r[:,1].mean():.1f} draft tokens verified, "
              f"{r[:,2].mean():.0f} SPARK draft cycles")
        out["results"][name] = {"tok_per_pass": r[:, 0].mean(), "draft_tokens": r[:, 1].mean(), "draft_cycles": r[:, 2].mean()}
    POL = {"software copy, best fixed k": (["copy"], "fixed"), "SPARK full, best fixed k": (["full"], "fixed"),
           "copy+SPARK fast, best fixed k": (["copy", "fast"], "fixed"),
           "copy+SPARK fast, confidence-chosen k": (["copy", "fast"], "adapt"),
           "copy+SPARK full, confidence-chosen k": (["copy", "full"], "adapt")}
    out["batch"] = []
    for gname, g in GPUS.items():
        print(f"\n{gname}, 9B model: speed-up vs plain decode (fixed k and lambda picked on calibration half, shown on test)")
        print(f"  {'batch':>5s} " + " ".join(f"{p[:24]:>25s}" for p in POL) + "   SPARK chips needed (fast)")
        for B in (1, 4, 16, 64, 256):
            line, row = f"  {B:5d} ", {"gpu": gname, "batch": B}
            for pname, (how, mode) in POL.items():
                chips = 1
                if mode == "fixed":
                    best = max(range(0, KMAX + 1), key=lambda k: speed(policy(cal, T, how, k=k), g, B, ingest_cyc, bpt, 64)[0]
                               if k else 1.0)
                    r = policy(test, T, how, k=best) if best else np.tile([1, 0, 0], (len(test), 1)).astype(float)
                else:
                    best = max(np.linspace(0, 2.0, 41), key=lambda lm: speed(policy(cal, T, how, lam=lm), g, B, ingest_cyc, bpt, 64)[0])
                    r = policy(test, T, how, lam=best)
                need = 1
                ic = 0 if "software" in pname else CYC_RECALL if "fast" in pname else ingest_cyc
                while speed(r, g, B, ic, bpt, need)[3] > 0.1 and need < 4096:   # SPARK time <= 10% of pass time
                    need *= 2
                sp = speed(r, g, B, ic, bpt, need)[0]
                line += f"{sp:24.2f}x "
                row[pname] = {"speedup": sp, "param": float(best), "chips": need}
            fast_chips = row["copy+SPARK fast, confidence-chosen k"]["chips"]; full_chips = row["copy+SPARK full, confidence-chosen k"]["chips"]
            print(line + f"  fast {fast_chips}, full {full_chips}")
            out["batch"].append(row)
    json.dump(out, open(os.path.join(HERE, "..", "results", "draft_v4%s.json" % ("_hyst" if os.environ.get("POLICY") == "hyst" else "")), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
