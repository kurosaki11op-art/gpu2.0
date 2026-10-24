"""Few-shot baseline with PRETRAINED features (24 Oct 2026, MEASURED on CPU): ImageNet-pretrained ResNet-18 (timm resnet18.a1_in1k) on images upsampled to 64x64 and replicated to 3 channels;
labelled examples drawn from the first 20,000 training images, tested on all 10,000 test images; class-mean cosine (prototype), logistic regression, 1-NN. 3 draws per n.
This uses a network trained on 1.28 M labelled ImageNet images, so it is NOT label-free; it shows the ceiling a few-shot method with outside data reaches. usage: python pretrained_fewshot.py DATA_DIR fashion|mnist"""
import sys, numpy as np, torch, torch.nn as nn, timm
sys.path.insert(0, "/home/user/gpu2.0/hw/brain"); from cortex_core import load
torch.set_num_threads(2); D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NP = 20000
net = timm.create_model("resnet18.a1_in1k", pretrained=True, num_classes=0).eval(); mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1); std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
def feats(x):
    out = []
    with torch.no_grad():
        for i in range(0, len(x), 250):
            t = torch.tensor(x[i:i + 250].reshape(-1, 1, 28, 28).astype(np.float32) / 255.0); t = nn.functional.interpolate(t, size=64, mode="bilinear").repeat(1, 3, 1, 1); out.append(net((t - mean) / std))
    return torch.cat(out)
ftr, fte = feats(xtr[:NP]), feats(xte); ytr = ytr[:NP]; print("features", ftr.shape, flush=True)
mu, sd = ftr.mean(0), ftr.std(0) + 1e-3; ftr_n, fte_n = (ftr - mu) / sd, (fte - mu) / sd
yt = torch.tensor(yte)
def proto(idx):
    P = torch.stack([ftr_n[idx][ytr[idx] == c].mean(0) for c in range(10)]); P = P / P.norm(dim=1, keepdim=True); q = fte_n / fte_n.norm(dim=1, keepdim=True); return ((q @ P.T).argmax(1) == yt).float().mean().item()
def logreg(idx):
    torch.manual_seed(0); X = ftr_n[idx]; Y = torch.tensor(ytr[idx]); m = nn.Linear(X.shape[1], 10); opt = torch.optim.Adam(m.parameters(), 1e-2, weight_decay=1e-2)
    for _ in range(200): loss = nn.functional.cross_entropy(m(X), Y); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return (m(fte_n).argmax(1) == yt).float().mean().item()
def nn1(idx):
    A = ftr_n[idx]; A = A / A.norm(dim=1, keepdim=True); q = fte_n / fte_n.norm(dim=1, keepdim=True); return (torch.tensor(ytr[idx])[(q @ A.T).argmax(1)] == yt).float().mean().item()
meths = {"pretrained ResNet-18: class means": proto, "pretrained ResNet-18: logistic regression": logreg, "pretrained ResNet-18: 1-NN": nn1}
print("| labelled examples per class | " + " | ".join(meths) + " |\n|---|" + "---|" * len(meths), flush=True)
for n in (1, 2, 5, 10, 20, 50, 100, 300):
    res = {k: [] for k in meths}
    for seed in range(3):
        r = np.random.RandomState(1000 + seed); idx = np.concatenate([r.choice(np.where(ytr == c)[0], n, replace=False) for c in range(10)])
        for k, f in meths.items(): res[k].append(f(idx))
    print("| %d | " % n + " | ".join("%.1f +- %.1f" % (100 * np.mean(v), 100 * np.std(v)) for v in res.values()) + " |", flush=True)
