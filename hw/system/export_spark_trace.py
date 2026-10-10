"""Export the held-out test text and SPARK v2's per-byte outputs (prediction, path pin, calibrated confidence)
for local_llm_test.py, so the big-model test can run on any PC without the SPARK code.
SPARK side: bit-exact v2 golden model (multi-order recall + RLCD confidence LUT), out_qat_sp0.05 weights."""
import base64, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "train")); sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa: E402
data = tr.load_corpus(3_000_000); n = len(data)
test = data[int(n * 0.95): int(n * 0.95) + 20000]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0,
                          exit_en=1, exit_th=16), tb=12, lut=lut)
r = [g.step(int(b)) for b in test]
out = {"note": "SPARK v2 golden model outputs; pred[i] and conf[i] are SPARK's guess and confidence for byte i+1",
       "text_b64": base64.b64encode(bytes(test)).decode(),
       "pred_hex": bytes(o["pred"] for o in r).hex(),
       "path": "".join(str(o["path"]) for o in r),
       "conf_hex": bytes(o["conf"] for o in r).hex()}
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "data", "spark_trace.json"), "w"))
print("wrote", len(test), "bytes; SPARK accuracy", np.mean(np.array([o["pred"] for o in r])[:-1] == test[1:]))
