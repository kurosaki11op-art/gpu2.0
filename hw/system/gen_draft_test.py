"""Draft mode on GPU-generated text (the realistic case: SPARK reads what the GPU writes, so its recall memory learns
the GPU's own habits). Lossless speculative sampling: SPARK drafts deterministic bytes; the GPU accepts draft byte x
with probability p_gpu(x) (draft prob q = 1), so output is distributed exactly as the GPU alone.
Expected bytes per GPU pass for a draft of length j: sum_{k=0..j} prod_{m<k} p_m (+1 byte from the GPU itself).
Compared on human-written text vs GPU-generated text."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
from model import GPT, GPTConfig  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
torch.manual_seed(0)
N, T = 20000, float(sys.argv[1]) if len(sys.argv) > 1 else 0.8

# 1) GPU generates text (sampling at temperature T), prompted with real code; keep its distributions
human = Z["test_text"]
seq = [int(v) for v in human[:128]]; probs_at = []
with torch.no_grad():
    while len(seq) < N + 128:
        x = torch.tensor(seq[-128:])[None]
        lg, _ = m(x)
        p = torch.softmax(lg[0, -1] / T, -1)
        nxt = int(torch.multinomial(p, 1))
        probs_at.append(p.numpy()); seq.append(nxt)
gen = np.array(seq[128:], np.int64); P = np.stack(probs_at)          # P[i] = GPU distribution for gen[i]


def spark_run(d):
    g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16), tb=12, lut=lut)
    r = [g.step(int(b)) for b in d]
    return np.array([o["pred"] for o in r]), np.array([o["conf"] for o in r]) / 255.0


def spec(paccept, conf, th, K=32, seed=0):
    """simulated lossless speculative sampling: each drafted byte is accepted with prob p_gpu(draft byte); at the first
    rejection (or end of draft) the GPU emits one byte itself. Returns output bytes per GPU pass."""
    rng = np.random.default_rng(seed)
    n = len(paccept); i = 0; passes = 0; out = 0
    while i < n:
        j, cum = 0, 1.0
        while j < K and i + j < n and cum * conf[i + j] >= th:
            cum *= conf[i + j]; j += 1
        a = 0
        while a < j and rng.random() < paccept[i + a]:
            a += 1
        i += a + 1; out += a + 1; passes += 1
    return out / passes


res = {}
# human text: acceptance prob = GPU prob of SPARK's guess (cached, temperature 1); for fairness recompute at T
sp_g, cf_g = spark_run(gen)
acc_gen = np.array([P[i + 1][sp_g[i]] if i + 1 < len(P) else 0 for i in range(len(gen))])  # SPARK's guess for gen[i+1]
acc_hum = Z["test_big_psp"]; cf_h = Z["test_conf"]
print(f"GPU temperature {T}: SPARK agrees with the GPU's own most likely byte: human text {np.mean(Z['test_sp'][:-1]==Z['test_big_pred'][:-1]):.1%}, "
      f"GPU-generated text {np.mean(sp_g[:-1]==np.array([P[i+1].argmax() for i in range(len(gen)-1)])):.1%}")
print(f"mean acceptance probability of SPARK's guess: human text {acc_hum.mean():.2f}, GPU-generated text {acc_gen.mean():.2f}")
for th in (0.1, 0.2, 0.3, 0.5):
    h = spec(acc_hum, cf_h, th); gg = spec(acc_gen, cf_g, th)
    print(f"  draft threshold {th}: bytes per GPU pass  human text {h:.2f} | GPU-generated text {gg:.2f}  (byte-level GPU alone = 1.00)")
    res[str(th)] = {"human": h, "generated": gg}
res["agree_human"] = float(np.mean(Z['test_sp'][:-1] == Z['test_big_pred'][:-1]))
res["accept_human"] = float(acc_hum.mean()); res["accept_generated"] = float(acc_gen.mean())
json.dump(res, open(os.path.join(HERE, "..", "results", f"draft_generated_T{T}.json"), "w"), indent=1)
