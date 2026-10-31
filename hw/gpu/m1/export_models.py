#!/usr/bin/env python3
"""M1 exporter and mapper (31 Oct 2026). Trains a small character-level decoder (2 layers, d=256, 4 heads, context 64) and a small convolutional network (Fashion-MNIST), writes for each:
tensors.bin + manifest.txt (weights), program.txt (our instruction list, see hw/gpu/ISA_M1.md), inputs.bin + input.txt, ref.bin (PyTorch fp32 outputs), analytic.json (MACs and SRAM bytes from the model dimensions).
usage: python export_models.py OUTDIR   (OUTDIR/lm and OUTDIR/cnn are created)"""
import json, os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "brain")); torch.set_num_threads(4)
OUT = sys.argv[1]; V, D, H, NL, T, FF = 128, 256, 4, 2, 64, 1024; TILE_BYTES = 4 * 1024 * 1024

class Block(nn.Module):
    def __init__(s):
        super().__init__(); s.ln1 = nn.LayerNorm(D, eps=1e-5); s.q = nn.Linear(D, D); s.k = nn.Linear(D, D); s.v = nn.Linear(D, D); s.o = nn.Linear(D, D); s.ln2 = nn.LayerNorm(D, eps=1e-5); s.f1 = nn.Linear(D, FF); s.f2 = nn.Linear(FF, D)
    def forward(s, x):
        B, t, _ = x.shape; h = s.ln1(x); q, k, v = [m(h).view(B, t, H, D // H).transpose(1, 2) for m in (s.q, s.k, s.v)]
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True).transpose(1, 2).reshape(B, t, D); x = x + s.o(a)
        return x + s.f2(F.gelu(s.f1(s.ln2(x)), approximate="tanh"))

class LM(nn.Module):
    def __init__(s): super().__init__(); s.tok = nn.Embedding(V, D); s.pos = nn.Embedding(T, D); s.blocks = nn.ModuleList([Block() for _ in range(NL)]); s.lnf = nn.LayerNorm(D, eps=1e-5); s.head = nn.Linear(D, V)
    def forward(s, ids):
        x = s.tok(ids) + s.pos(torch.arange(ids.shape[1])[None])
        for b in s.blocks: x = b(x)
        return s.head(s.lnf(x))

class Net(nn.Module):
    def __init__(s): super().__init__(); s.c1 = nn.Conv2d(1, 16, 3); s.c2 = nn.Conv2d(16, 32, 3); s.fc = nn.Linear(800, 10)
    def forward(s, x): x = F.max_pool2d(F.relu(s.c1(x)), 2); x = F.max_pool2d(F.relu(s.c2(x)), 2); return s.fc(x.flatten(1))

class Store:
    def __init__(s): s.items, s.off = [], 0
    def add(s, name, a): a = np.ascontiguousarray(np.asarray(a, np.float32)); s.items.append((name, s.off, a)); s.off += a.size
    def write(s, d):
        os.makedirs(d, exist_ok=True); open(os.path.join(d, "tensors.bin"), "wb").write(b"".join(a.tobytes() for _, _, a in s.items))
        open(os.path.join(d, "manifest.txt"), "w").write("\n".join("%s %d %d %s" % (n, o, a.ndim, " ".join(map(str, a.shape))) for n, o, a in s.items) + "\n")

def lm_data():
    from datasets import load_dataset
    txt = "\n".join(load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="train")["text"])[:3_000_000]; ids = np.frombuffer(txt.encode("ascii", "ignore"), np.uint8).astype(np.int64) % V; return torch.tensor(ids)

def build_lm():
    d = os.path.join(OUT, "lm"); data = lm_data(); torch.manual_seed(0); m = LM(); opt = torch.optim.AdamW(m.parameters(), 1e-3, weight_decay=0.01); t0 = time.time(); steps = 900
    for step in range(steps):
        ix = torch.randint(0, len(data) - T - 1, (48,)); x = torch.stack([data[i:i + T] for i in ix]); y = torch.stack([data[i + 1:i + T + 1] for i in ix])
        loss = F.cross_entropy(m(x).view(-1, V), y.view(-1)); opt.zero_grad(); loss.backward(); opt.step()
        if step % 150 == 0: print("lm step", step, "loss %.3f" % loss.item(), "%.0fs" % (time.time() - t0), flush=True)
    m.eval(); st = Store(); sd = {k: v.detach().numpy() for k, v in m.state_dict().items()}
    st.add("tok", sd["tok.weight"]); st.add("pos", sd["pos.weight"]); st.add("posidx", np.arange(T, dtype=np.float32))
    for l in range(NL):
        p = "blocks.%d." % l
        for nm, k in (("ln1g", "ln1.weight"), ("ln1b", "ln1.bias"), ("ln2g", "ln2.weight"), ("ln2b", "ln2.bias")): st.add("L%d.%s" % (l, nm), sd[p + k])
        for nm, k in (("wq", "q"), ("wk", "k"), ("wv", "v"), ("wo", "o"), ("w1", "f1"), ("w2", "f2")): st.add("L%d.%s" % (l, nm), sd[p + k + ".weight"].T); st.add("L%d.b%s" % (l, nm[1:]), sd[p + k + ".bias"])
    st.add("lnfg", sd["lnf.weight"]); st.add("lnfb", sd["lnf.bias"]); st.add("headw", sd["head.weight"].T); st.add("headb", sd["head.bias"]); st.write(d)
    prog, tile = ["GATHER x0 tok ids 0 #emb", "GATHER p0 pos posidx 0 #emb", "ADD x x0 p0 #emb"], 0
    for l in range(NL):
        t = l + 1; g = "L%d." % l
        prog += ["LN h x %sln1g %sln1b #L%d.attn" % (g, g, l)]
        for n in "qkv": prog.append("MM %s h %sw%s %sb%s %d #L%d.attn" % (n, g, n, g, n, t, l))
        prog += ["ATTN a q k v %d %d #L%d.attn" % (H, t, l), "MM o a %swo %sbo %d #L%d.attn" % (g, g, t, l), "ADD x x o #L%d.attn" % l, "LN h x %sln2g %sln2b #L%d.mlp" % (g, g, l),
                 "MM u h %sw1 %sb1 %d #L%d.mlp" % (g, g, t, l), "GELU u u #L%d.mlp" % l, "MM dn u %sw2 %sb2 %d #L%d.mlp" % (g, g, t, l), "ADD x x dn #L%d.mlp" % l]
    prog += ["LN x x lnfg lnfb #head", "MM logits x headw headb %d #head" % (NL + 1)]
    wtile = {"tok": 0, "pos": 0, "posidx": 0}
    for l in range(NL):
        for nm in ("wq", "wk", "wv", "wo", "w1", "w2"): wtile["L%d.%s" % (l, nm)] = l + 1
    wtile["headw"] = NL + 1
    head = ["W %s %d" % (n, t) for n, t in wtile.items() if n not in ("tok", "pos", "posidx")] + ["W tok 0", "W pos 0"]
    open(os.path.join(d, "program.txt"), "w").write("\n".join(head + prog) + "\n")
    # inputs: 16 windows of 64 characters from held-out text (the end of the corpus file is unseen by the 3M-character training prefix)
    full = "\n".join(__import__("datasets").load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")["text"]); tid = torch.tensor(np.frombuffer(full.encode("ascii", "ignore"), np.uint8).astype(np.int64) % V)
    ids = torch.stack([tid[i * 4001:i * 4001 + T] for i in range(16)]); ids.numpy().astype(np.float32).tofile(os.path.join(d, "inputs.bin")); open(os.path.join(d, "input.txt"), "w").write("ids %d\n" % T)
    with torch.no_grad(): ref = m(ids).numpy().astype(np.float32)
    ref.tofile(os.path.join(d, "ref.bin"))
    # analytic counts from the model dimensions (independent of the program)
    attn_mac = D * T * (T + 1); lay = {"emb": dict(macs=0), "head": dict(macs=T * D * V)}
    for l in range(NL): lay["L%d.attn" % l] = dict(macs=T * D * 3 * D + attn_mac + T * D * D); lay["L%d.mlp" % l] = dict(macs=2 * T * D * FF)
    json.dump(dict(per_tag=lay, total_macs=sum(v["macs"] for v in lay.values()), positions=int(ids.numel()), params_weights=int(sum(a.size for n, _, a in st.items if n not in ("posidx",)))), open(os.path.join(d, "analytic.json"), "w"), indent=1)
    print("lm exported; reference logits", ref.shape)

def build_cnn():
    from cortex_core import load
    d = os.path.join(OUT, "cnn"); xtr, ytr, xte, yte = load("/tmp/fashion", "fashion"); X = torch.tensor(xtr.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); Y = torch.tensor(ytr.astype(np.int64)); torch.manual_seed(0); m = Net(); opt = torch.optim.Adam(m.parameters(), 1e-3)
    for ep in range(3):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 64): b = p[i:i + 64]; opt.zero_grad(); F.cross_entropy(m(X[b]), Y[b]).backward(); opt.step()
        print("cnn epoch", ep, flush=True)
    m.eval(); st = Store(); sd = {k: v.detach().numpy() for k, v in m.state_dict().items()}
    st.add("c1w", sd["c1.weight"].reshape(16, -1).T); st.add("c1b", sd["c1.bias"]); st.add("c2w", sd["c2.weight"].reshape(32, -1).T); st.add("c2b", sd["c2.bias"]); st.add("fcw", sd["fc.weight"].T); st.add("fcb", sd["fc.bias"]); st.write(d)
    prog = ["W c1w 0", "W c2w 1", "W fcw 2", "CONV a1 x c1w c1b 1 3 3 0 #conv1", "RELU a1 a1 #conv1", "MAXPOOL2 a1 a1 #conv1", "CONV a2 a1 c2w c2b 16 3 3 1 #conv2", "RELU a2 a2 #conv2", "MAXPOOL2 a2 a2 #conv2", "FLATTEN f a2 #fc", "MM logits f fcw fcb 2 #fc"]
    open(os.path.join(d, "program.txt"), "w").write("\n".join(prog) + "\n")
    xs = torch.tensor(xte[:1000].reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); xs.numpy().tofile(os.path.join(d, "inputs.bin")); open(os.path.join(d, "input.txt"), "w").write("x 1 1 28 28\n")
    with torch.no_grad(): ref = m(xs).numpy().astype(np.float32)
    ref.tofile(os.path.join(d, "ref.bin")); np.save(os.path.join(d, "labels.npy"), yte[:1000]); mac = {"conv1": 26 * 26 * 16 * 9, "conv2": 11 * 11 * 32 * 16 * 9, "fc": 800 * 10}
    json.dump(dict(per_tag={k: dict(macs=v) for k, v in mac.items()}, total_macs=sum(mac.values()), positions=1000), open(os.path.join(d, "analytic.json"), "w"), indent=1); print("cnn exported; fp32 accuracy on the 1,000 images: %.4f" % float((ref.argmax(1) == yte[:1000]).mean()))

def selftest():
    d = os.path.join(OUT, "selftest"); rng = np.random.RandomState(0); a = rng.randn(8, 16).astype(np.float32); w = rng.randn(16, 8).astype(np.float32); b = rng.randn(8).astype(np.float32)
    st = Store(); st.add("w", w); st.add("b", b); st.write(d); open(os.path.join(d, "program.txt"), "w").write("W w 0\nMM y x w b 0 #t\n"); a.tofile(os.path.join(d, "inputs.bin")); open(os.path.join(d, "input.txt"), "w").write("x 8 16\n")
    sa = np.abs(a).max(1, keepdims=True) / 127.0; sw = np.abs(w).max(0, keepdims=True) / 127.0; qa = np.round(a / sa).clip(-127, 127); qw = np.round(w / sw).clip(-127, 127)
    (qa @ qw * sa * sw + b).astype(np.float32).tofile(os.path.join(d, "ref_int8.bin")); (a @ w + b).astype(np.float32).tofile(os.path.join(d, "ref.bin"))

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); selftest(); build_cnn(); build_lm()
