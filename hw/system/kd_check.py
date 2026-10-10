import json, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
for name, path in (("original", "out_qat_sp0.05"), ("distilled from GPU", "out_kd_big")):
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", path, "spark_v0_model.npz"))
    for split in ("test",):
        d = Z[f"{split}_text"]; gp = Z[f"{split}_big_pred"]
        g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16), tb=12, lut=lut)
        r = [g.step(int(b)) for b in d]; sp = np.array([o["pred"] for o in r]); pa = np.array([o["path"] for o in r])
        net = pa != 2
        print(f"{name:20s}: SPARK vs text {np.mean(sp[:-1]==d[1:]):.1%} | agrees with GPU {np.mean(sp[:-1]==gp[:-1]):.1%} "
              f"(network-answered bytes {net.mean():.0%}: agree {np.mean(sp[:-1][net[:-1]]==gp[:-1][net[:-1]]):.1%}, "
              f"recall-answered: agree {np.mean(sp[:-1][~net[:-1]]==gp[:-1][~net[:-1]]):.1%})")
