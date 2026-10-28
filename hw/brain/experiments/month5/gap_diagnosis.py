"""28 Oct 2026, SIMULATED (accuracy). WHERE DOES THE GAP TO A CNN COME FROM? Three measurements on Fashion-MNIST:
(1) per-class recall and the biggest confusions of the shipped system (L + L Deep, integer scores from the RTL memory files);
(2) the information in L's 4,608-bit code: an UNRESTRICTED small network (4608-256-10, float, dropout) trained on the code; if it is near the system's 89.7% the code is the limit, if it is near a CNN the readout is the limit;
(3) reference baselines on the raw pixels, labelled as references, not parts of L: the same 784-256-10 network, and a small CNN (2 conv layers).
All trained on the 60,000 training images, scored on the 10,000 test images, one seed each."""
import os, sys, time
import numpy as np
sys.argv = ["x", "/tmp/fashion"]; sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
from shirt_new_methods_setup import ctr, cte, xtr, xte, ytr, yte, NAMES
import ldeep_ref as R
import torch, torch.nn as nn
torch.manual_seed(0); torch.set_num_threads(3); t0 = time.time()
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X = np.ascontiguousarray(z["X"], np.uint8); rr, S, pp = R.run(X)
print("(1) shipped system L + L Deep: accuracy %.4f" % (pp == yte).mean())
cm = np.zeros((10, 10), int)
for a, b in zip(yte, pp): cm[a, b] += 1
tot_err = (pp != yte).sum()
print("%-12s %7s %8s  %-s" % ("class", "recall", "errors", "biggest confusions (class -> predicted, count)"))
for c in range(10):
    o = [(cm[c, j], j) for j in range(10) if j != c]; o.sort(reverse=True)
    print("%-12s %7.3f %7.1f%%  %s" % (NAMES[c], cm[c, c] / cm[c].sum(), 100 * (cm[c].sum() - cm[c, c]) / tot_err, ", ".join("%s %d" % (NAMES[j], n) for n, j in o[:2])))
pairs = {}
for a in range(10):
    for b in range(a + 1, 10): pairs[(a, b)] = cm[a, b] + cm[b, a]
top = sorted(pairs.items(), key=lambda kv: -kv[1])[:4]; print("top confused pairs (both directions): " + "; ".join("%s/%s %d (%.0f%% of all errors)" % (NAMES[a], NAMES[b], n, 100 * n / tot_err) for (a, b), n in top), flush=True)
def train_mlp(Xa, Xb, hidden=256, epochs=15, drop=0.3, tag=""):
    net = nn.Sequential(nn.Dropout(0.1), nn.Linear(Xa.shape[1], hidden), nn.ReLU(), nn.Dropout(drop), nn.Linear(hidden, 10)); opt = torch.optim.Adam(net.parameters(), lr=1e-3); A = torch.tensor(Xa, dtype=torch.float32); y = torch.tensor(ytr)
    for ep in range(epochs):
        net.train(); perm = torch.randperm(len(y))
        for i in range(0, len(y), 256):
            ix = perm[i:i + 256]; opt.zero_grad(); nn.functional.cross_entropy(net(A[ix]), y[ix]).backward(); opt.step()
    net.eval(); p = net(torch.tensor(Xb, dtype=torch.float32)).argmax(1).numpy(); a = (p == yte).mean(); print("%-52s %.4f [%.0fs]" % (tag, a, time.time() - t0), flush=True); return p
print("(2) information in the code (unrestricted network on L's 4,608-bit code, float):")
train_mlp(ctr, cte, tag="  MLP 4608-256-10 on L's code")
print("(3) reference baselines on raw pixels (NOT parts of L):")
train_mlp(xtr / 255.0, xte / 255.0, tag="  MLP 784-256-10 on raw pixels")
cnn = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 49, 10))
opt = torch.optim.Adam(cnn.parameters(), lr=1e-3); A = torch.tensor(xtr.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); y = torch.tensor(ytr)
for ep in range(8):
    cnn.train(); perm = torch.randperm(len(y))
    for i in range(0, len(y), 256):
        ix = perm[i:i + 256]; opt.zero_grad(); nn.functional.cross_entropy(cnn(A[ix]), y[ix]).backward(); opt.step()
cnn.eval(); p = cnn(torch.tensor(xte.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)).argmax(1).numpy(); print("  small CNN (2 conv layers, 8 epochs) on raw pixels        %.4f [%.0fs]" % ((p == yte).mean(), time.time() - t0), flush=True)
