"""MODELLED energy per token from MEASURED operation counts (bit-exact golden model, which the RTL matches).

Operation counts per token come from the golden model: which stages run, how many input events each stage
processes (each event reads nout/P weight words and does nout multiply-accumulates), the membrane/argmax pass
over every output neuron of each stage that runs, and recall-table accesses.

Energy per operation: Horowitz, "Computing's energy problem", ISSCC 2014 (45 nm):
  8 KB SRAM read, 64 bit: 10 pJ  -> 5 pJ per 32-bit weight word (8 int4 weights)
  8-bit multiply 0.2 pJ, 8-bit add 0.03 pJ, 32-bit add 0.1 pJ -> int4 x 3-bit MAC into 16 bit: ~0.1 pJ
  DRAM read: 1.3-2.6 nJ per 64 bit -> ~640 pJ per 32-bit word (off-chip weights, GPU-style large models)
Neuron pass: 3 x 16-bit SRAM accesses (acc, membrane read/write) at 2.5 pJ = 7.5 pJ per neuron (conservative).
Low/high bounds: MAC and neuron-pass energy x0.5 / x2.
Usage: python3 energy_model.py <model.npz> <out.json> [bytes]
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden")); sys.path.insert(0, os.path.join(HERE, "..", "train"))
import spark_golden as sg, train_spark_v0 as tr

E_WORD, E_MAC, E_NEURON, E_DRAM_WORD, E_RECALL = 5.0, 0.1, 7.5, 640.0, 4 * 5.0
NOUT = [sg.H, sg.H, sg.V, sg.V]


def counts(W, cfg, text):
    g = sg.Golden(W, cfg)
    ran = []
    orig = g._events
    def rec(k, src):
        ran[-1].append(k)
        return orig(k, src)
    g._events = rec
    rows = []
    for b in text:
        ran.append([])
        o = g.step(int(b))
        rows.append((o["pred"], o["path"], list(o["proc"]), list(ran[-1])))
    return rows


def energy(rows, recall, mac=E_MAC, neuron=E_NEURON, word=E_WORD):
    tot = 0.0; words = 0
    for _, _, proc, ran in rows:
        for k in ran:
            w = proc[k] * NOUT[k] // sg.P
            words += w
            tot += w * word + proc[k] * NOUT[k] * mac + NOUT[k] * neuron
        tot += E_RECALL if recall else 0
    return tot / len(rows), words / len(rows)


def main():
    npz, out = sys.argv[1], sys.argv[2]
    nb = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    W = sg.Weights.from_npz(npz)
    data = tr.load_corpus(3_000_000); n = len(data)
    test = data[int(n * 0.95): int(n * 0.95) + nb]
    base = dict(spike_mode="thr")
    ev = json.load(open(os.path.join(os.path.dirname(npz), "system_eval.json")))
    xt, at = ev["exit_th"], ev.get("arb_th", 128)
    ad = dict(adapt=1, recall=1, conf_th=0, exit_en=1, exit_th=xt)
    configs = [
        ("dense: every input, every neuron (GPU-style)", dict(sparse=0), 0),
        ("event-driven: skip silent neurons", dict(sparse=1), 0),
        ("SPARK effort LOW (memory answers, skip network)", dict(ad, recall_mode=0), 1),
        ("SPARK effort MEDIUM (memory answers, neurons updated)", dict(ad, recall_mode=1), 1),
        ("SPARK effort HIGH (network can overrule memory)", dict(ad, recall_mode=2, arb_th=at), 1),
    ]
    res = []
    for name, ov, rc in configs:
        rows = counts(W, sg.Cfg(**base, **ov), test)
        acc = float(np.mean(np.array([r[0] for r in rows[:-1]]) == test[1:]))
        e, wds = energy(rows, rc)
        lo, _ = energy(rows, rc, E_MAC * 0.5, E_NEURON * 0.5)
        hi, _ = energy(rows, rc, E_MAC * 2, E_NEURON * 2)
        dram, _ = energy(rows, rc, word=E_DRAM_WORD)
        res.append(dict(config=name, accuracy=acc, weight_words_per_token=wds, pJ_per_token=e,
                        pJ_low=lo, pJ_high=hi, pJ_if_weights_in_DRAM=dram))
        print(f"{name:55s} acc {acc:.1%}  words {wds:7.0f}  {e / 1000:7.2f} nJ/token  "
              f"(DRAM weights {dram / 1000:8.1f} nJ)", flush=True)
    d = res[0]
    for r in res:
        r["x_less_energy_vs_dense"] = d["pJ_per_token"] / r["pJ_per_token"]
        r["x_range"] = [d["pJ_low"] / r["pJ_low"], d["pJ_high"] / r["pJ_high"]]
        r["x_less_energy_vs_dense_DRAM"] = d["pJ_if_weights_in_DRAM"] / r["pJ_if_weights_in_DRAM"]
    json.dump(dict(model=npz, eval_bytes=nb, results=res), open(out, "w"), indent=2)


if __name__ == "__main__":
    main()
