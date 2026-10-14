"""Harder protocol: 10 stages of ONE new class each (integer chip model, month-2 rule) vs a fine-tuned network.
usage: python stages10.py DATA_DIR mnist|fashion|speech"""
import json, os, sys
import numpy as np, torch
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
F = 64 if DS == "speech" else 32
z = np.load(os.path.join(D, f"sep_{DS}_F{F}_p2.npz")); ctr, cte = z["tr"], z["te"]
if DS == "speech":
    import cochlea
    xtr, ytr, xte, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"), cochlea.sound_picture_res)
else:
    xtr, ytr, xte, yte = load(D, DS)
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
m = CortexInt(ctr.shape[1], B=10, night=2, daydream=1, night_stop=2); chip = []
torch.manual_seed(0); net = torch.nn.Sequential(torch.nn.Linear(784, 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
opt = torch.optim.Adam(net.parameters(), 1e-3); nn_acc = []
for c in range(10):
    sel = np.where(ytr == c)[0]; sel = sel[np.random.RandomState(c).permutation(len(sel))]
    m.stage(ctr[sel], ytr[sel]); seen = yte <= c
    chip.append(float((m.predict(cte[seen]) == yte[seen]).mean()))
    X = torch.tensor(xtr[sel] / 255.0, dtype=torch.float32); Y = torch.tensor(ytr[sel])
    for _ in range(2):
        for b in torch.randperm(len(X)).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(net(X[b]), Y[b]).backward(); opt.step()
    with torch.no_grad():
        nn_acc.append(float((net(torch.tensor(xte[seen] / 255.0, dtype=torch.float32)).argmax(1).numpy() == yte[seen]).mean()))
    print(DS, "stage", c + 1, "chip %.4f  network %.4f" % (chip[-1], nn_acc[-1]), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED", "chip": chip, "network_finetuned": nn_acc},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_stages10_{DS}.json"), "w"), indent=1)
