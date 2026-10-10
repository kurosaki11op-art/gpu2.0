"""Idea D: SPARK as a request-difficulty router (chip design unchanged).
Split held-out text into 'requests' (256-byte chunks). SPARK's mean calibrated confidence over a chunk is its
difficulty estimate. Check how well it predicts the GPU model's real difficulty (bits/byte) and whether routing the
easiest chunks to a small model keeps quality. Small model here = SPARK's own answers (the cheapest model)."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa
data = tr.load_corpus(3_000_000); n = len(data); test = data[int(n * 0.95): int(n * 0.95) + 20000]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16), tb=12, lut=lut)
r = [g.step(int(b)) for b in test]
conf = np.array([o["conf"] for o in r]) / 255.0; sp = np.array([o["pred"] for o in r])
ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
x = torch.from_numpy(test.astype(np.int64)); nll = np.zeros(len(test)); gp = np.zeros(len(test), int)
with torch.no_grad():
    for s in range(0, len(test), 64):
        lo = max(0, s - 64); hi = min(len(test), s + 64)
        lg, _ = m(x[lo:hi][None], targets=x[lo:hi][None]); lp = torch.log_softmax(lg[0], -1)
        for i in range(s, hi - 1):
            nll[i] = -lp[i - lo, test[i + 1]].item() / np.log(2); gp[i] = int(lp[i - lo].argmax())
C = 256; k = (len(test) - 1) // C
mc = np.array([conf[i*C:(i+1)*C].mean() for i in range(k)])
hard = np.array([nll[i*C:(i+1)*C].mean() for i in range(k)])
gacc = np.array([np.mean(gp[i*C:(i+1)*C] == test[i*C+1:(i+1)*C+1]) for i in range(k)])
sacc = np.array([np.mean(sp[i*C:(i+1)*C] == test[i*C+1:(i+1)*C+1]) for i in range(k)])
rho = np.corrcoef(np.argsort(np.argsort(mc)), np.argsort(np.argsort(-hard)))[0, 1]
print(f"{k} requests; rank correlation SPARK confidence vs GPU-model easiness: {rho:.2f}")
order = np.argsort(-mc)
res = {"requests": int(k), "spearman": float(rho), "points": []}
for f in (0.1, 0.25, 0.5):
    e = order[:int(f * k)]; rest = order[int(f * k):]
    print(f"easiest {f:.0%} by SPARK: GPU bits/byte {hard[e].mean():.2f} vs rest {hard[rest].mean():.2f}; "
          f"SPARK alone on them {sacc[e].mean():.1%} vs GPU {gacc[e].mean():.1%}")
    res["points"].append(dict(fraction=f, gpu_bits_easy=float(hard[e].mean()), gpu_bits_rest=float(hard[rest].mean()),
                              spark_acc_easy=float(sacc[e].mean()), gpu_acc_easy=float(gacc[e].mean())))
json.dump(res, open(os.path.join(HERE, "..", "results", "idea_d_router.json"), "w"), indent=1)
