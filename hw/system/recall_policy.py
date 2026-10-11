"""Recall-memory policy study (SPARK v2 golden model, same table sizes and entry format).
update : replace  = current v2 rule (a mismatch overwrites the value, count 0)
         hyst     = a mismatch only decrements the 2-bit count; the value is replaced when the count is already 0
select : order    = current v2 rule (highest-order hit answers)
         count    = the hit with the highest count answers (ties -> higher order)
Metric: next-byte agreement with the GPU model's greedy prediction and mean agreement run length (draft-relevant)."""
import json, os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as g1, spark_golden_v2 as g2  # noqa


class Policy(g2.GoldenV2):
    def __init__(self, *a, update="replace", select="order", **k):
        super().__init__(*a, **k); self.update, self.select = update, select

    def step(self, b):
        c = self.c
        prev = self.hist6
        self.hist6 = ((prev << 8) | b) & ((1 << 48) - 1)
        for k in range(len(self.orders)):
            i, tag = self._slot(k, prev)
            e = self.tables[k].get(i)
            if e and e[0] == tag:
                if e[1] == b:
                    e = [tag, b, min(e[2] + 1, 3)]
                elif self.update == "hyst" and e[2] > 0:
                    e = [tag, e[1], e[2] - 1]
                else:
                    e = [tag, b, 0]
            else:
                e = [tag, b, 0]
            self.tables[k][i] = e
        hits = []
        for k in reversed(range(len(self.orders))):
            i, tag = self._slot(k, self.hist6)
            e = self.tables[k].get(i)
            if e and e[0] == tag and e[2] >= c.conf_th:
                hits.append((k, e[1], e[2]))
        self.last_alts = [h[1] for h in hits]
        if self.select == "count" and hits:
            hits.sort(key=lambda h: (-h[2], -h[0]))
        # reuse the parent's network/LUT path by temporarily faking the lookup result
        best = None
        if hits:
            k, v, cnt = hits[0]; others = [h[1] for h in hits[1:]]
            best = (k, v, cnt, 1 if not others else (2 if v in others else 0))
        return self._finish(b, best)

    def _finish(self, b, best):
        c = self.c
        out = {"ev": [0, 0, 0, 0], "proc": [0, 0, 0, 0], "mexit": -1, "mmain": -1, "rbest": best}
        x_in = self._input(b); self.tok += 1
        if best is not None and c.recall_mode == 0:
            out.update(pred=best[1], path=2, bucket=best[0] * 12 + best[2] * 3 + best[3])
        else:
            def stage(k, src):
                out["ev"][k], out["proc"][k] = self._events(k, src)
            stage(0, x_in); self._membrane(0, 0); done = False
            if best is None and c.exit_en:
                stage(2, self.s[0]); idx, m = self._argmax(2)
                if m >= c.exit_th:
                    out.update(pred=idx, path=1, bucket=48 + g2.mbucket(m)); done = True
            if not done:
                stage(1, self.s[0]); self._membrane(1, 1); stage(3, self.s[1]); idx, m = self._argmax(3)
                if best is not None and m < c.arb_th:
                    out.update(pred=best[1], path=2, bucket=80 + g2.mbucket(m))
                else:
                    out.update(pred=idx, path=0, bucket=64 + g2.mbucket(m))
        out["conf"] = int(self.lut[out["bucket"]]); self.last = (out["bucket"], out["pred"])
        return out


if __name__ == "__main__":
    Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
    text, big = Z["test_text"], Z["test_big_pred"]; N = int(os.environ.get("NB", 8000))
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    rows = []
    for upd, sel, (mode, arb) in itertools.product(("replace", "hyst"), ("order", "count"), ((0, 16), (2, 64))):
        cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=mode, exit_en=1, exit_th=16)
        cfg.arb_th = arb
        g = Policy(W, cfg, tb=12, lut=lut, update=upd, select=sel)
        pred = np.array([g.step(int(b))["pred"] for b in text[:N]])
        ag = pred == big[:N]
        runs = np.diff(np.flatnonzero(np.concatenate([[1], ~ag, [1]]))) - 1
        r = dict(update=upd, select=sel, recall_mode=mode, arb_th=arb, agree_gpu=float(ag.mean()), mean_run=float(runs.mean()))
        rows.append(r); print(r, flush=True)
    json.dump(rows, open(os.path.join(HERE, "..", "results", "recall_policy.json"), "w"), indent=1)
