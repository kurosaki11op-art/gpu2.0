"""Export the held-out test text and SPARK's per-byte outputs (prediction + path pin) for ollama_test.py.
The SPARK side is the bit-exact golden model of the verified chip (out_qat_sp0.05 weights)."""
import base64, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "train")); sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as sg, train_spark_v0 as tr  # noqa: E402

SETTINGS = {
    "safe (recall conf>=1, exit>=64)": dict(recall=1, conf_th=1, recall_mode=0, exit_en=1, exit_th=64),
    "balanced (recall conf>=1, exit>=32)": dict(recall=1, conf_th=1, recall_mode=0, exit_en=1, exit_th=32),
    "aggressive (recall conf>=0, exit>=16)": dict(recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16),
}
data = tr.load_corpus(3_000_000); n = len(data)
test = data[int(n * 0.95): int(n * 0.95) + 20000]
W = sg.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
out = {"text_b64": base64.b64encode(bytes(test)).decode(), "settings": {}}
for k, ov in SETTINGS.items():
    g = sg.Golden(W, sg.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", **ov))
    r = [g.step(int(b)) for b in test]
    out["settings"][k] = {"pred": bytes(o["pred"] for o in r).hex(), "path": "".join(str(o["path"]) for o in r)}
json.dump(out, open(os.path.join(HERE, "data", "spark_trace.json"), "w"))
print("wrote", len(test), "bytes")
