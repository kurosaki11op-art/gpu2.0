"""Where does the 35-word accuracy limit sit? (19 Oct 2026) Same speaker-disjoint split of the 35-word Speech Commands subset, all 35 words learned together, accuracy on the held-out speakers. Diagnostic only, SIMULATED.
  chip table : CortexSlow (5-bit table, margin perceptron, dreams) on the finer-grid sparse code
  float linear / float MLP on the same sparse code  -> if much better than the table: readout / precision / learning-rule limit
  float CNN on the cochlea picture (28x28)           -> if much better than both: the sparse code itself is the limit
usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, torch
from sound_align_confirm import align
from cortex_slow import CortexSlow
torch.set_num_threads(4)
D = sys.argv[1]
z = np.load(os.path.join(D, "sc35_framesums_int.npz")); S, y, te = z["S"], z["y"].astype(int), z["te"]
codes = np.load(os.path.join(D, "sc35_codes_geom3311.npz"))["codes"]; P = align(S, 6)
tr_i, te_i = np.where(~te)[0], np.where(te)[0]; ytr, yte = y[tr_i], y[te_i]; print("train", len(tr_i), "test", len(te_i), "classes", y.max() + 1, flush=True)
accs = []
for s in (1, 2):
    m = CortexSlow(codes.shape[1], n_cls=64, ch=100, K=5, seed=s, night_stop=2, daydream=1); pp = np.random.RandomState(s).permutation(len(tr_i)); m.stage(codes[tr_i][pp], ytr[pp]); accs.append((m.predict(codes[te_i]) == yte).mean())
print(f"chip table (all 35 together): {np.mean(accs):.3f}", flush=True)
def fit(model, Xtr, Xte, ep, lr, wd=0.0, bs=64, seed=0):
    torch.manual_seed(seed); opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd); Xtr_t, ytr_t = torch.tensor(Xtr), torch.tensor(ytr)
    for e in range(ep):
        model.train(); perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), bs):
            b = perm[i:i + bs]; opt.zero_grad(); torch.nn.functional.cross_entropy(model(Xtr_t[b]), ytr_t[b]).backward(); opt.step()
    model.eval()
    with torch.no_grad(): return (model(torch.tensor(Xte)).argmax(1).numpy() == yte).mean()
Xc, nb = codes.astype(np.float32), codes.shape[1]
print(f"float linear on code: {fit(torch.nn.Linear(nb, 35), Xc[tr_i], Xc[te_i], 30, 1e-3):.3f}", flush=True)
print(f"float MLP (512) on code: {fit(torch.nn.Sequential(torch.nn.Linear(nb, 512), torch.nn.ReLU(), torch.nn.Dropout(0.3), torch.nn.Linear(512, 35)), Xc[tr_i], Xc[te_i], 30, 1e-3, wd=1e-2):.3f}", flush=True)
Xp = (P.reshape(len(P), 1, 28, 28).astype(np.float32) / 255.0)
cnn = lambda: torch.nn.Sequential(torch.nn.Conv2d(1, 32, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2), torch.nn.Conv2d(32, 64, 3, padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
                                  torch.nn.Flatten(), torch.nn.Dropout(0.3), torch.nn.Linear(64 * 49, 128), torch.nn.ReLU(), torch.nn.Linear(128, 35))
print(f"float CNN on the 28x28 cochlea picture: {fit(cnn(), Xp[tr_i], Xp[te_i], 30, 1e-3, wd=1e-2):.3f}", flush=True)
