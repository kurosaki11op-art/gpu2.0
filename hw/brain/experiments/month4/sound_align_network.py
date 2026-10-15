"""Fair check for word alignment: the same network baseline as the month-1/2 tables (MLP 784-256-10, Adam, 5 epochs,
as proof_suite_v3.mlp_fit), all words at once, on the chip's integer cochlea pictures with the noise floor, without
and with word alignment (lead 6). 3 seeds. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch
import cochlea_int
D = sys.argv[1]
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)


def mlp_fit(X, y, seed, ep=5):
    torch.manual_seed(seed)
    m = torch.nn.Sequential(torch.nn.Linear(X.shape[1], 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
    opt = torch.optim.Adam(m.parameters(), 1e-3); Xt = torch.tensor(X, dtype=torch.float32); Yt = torch.tensor(y)
    g = torch.Generator().manual_seed(seed)
    for _ in range(ep):
        for b in torch.randperm(len(Xt), generator=g).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(m(Xt[b]), Yt[b]).backward(); opt.step()
    return m


res = {}
for name, X in (("no_alignment", P), ("aligned_lead6", cochlea_int.align_word(P, 6))):
    X = X / 255.0; accs = []
    for s in (0, 1, 2):
        m = mlp_fit(X[~te], y[~te].astype(np.int64), s)
        with torch.no_grad():
            accs.append(round(float((m(torch.tensor(X[te], dtype=torch.float32)).argmax(1).numpy() == y[te]).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(name, res[name], flush=True)
json.dump({"label": "SIMULATED (MLP baseline, 3 seeds, all at once)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_align_network.json"), "w"), indent=1)
