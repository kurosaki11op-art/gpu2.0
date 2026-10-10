"""Idea C step 1: SPARK reads the whole training split and outputs its calibrated confidence for every byte."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden")); sys.path.insert(0, os.path.join(HERE, "..", "train"))
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa
data = tr.load_corpus(3_000_000); train = data[: int(len(data) * 0.9)]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16), tb=12, lut=lut)
conf = np.zeros(len(train), np.uint8)
for i, b in enumerate(train):
    conf[i] = g.step(int(b))["conf"]
    if i % 200000 == 0: print(i, flush=True)
np.save(os.path.join(HERE, "out", "train_conf.npy"), conf)
print("done", conf.mean() / 255)
