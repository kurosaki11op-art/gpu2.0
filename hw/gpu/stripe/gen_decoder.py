#!/usr/bin/env python3
"""Striping test S-c: writes a decode program and random weights for a scaled dense decoder (shape of the 1B reference divided by 4 in width: 16 layers, d 512, ff 2048, 4 heads, vocabulary 8000).
Latency does not depend on the weight values, so the weights are random (std 0.02); no accuracy claim is made.
usage: gen_decoder.py OUTDIR [STEPS] [D] [NL] [FF] [HEADS] [VOCAB]"""
import os, sys
import numpy as np
out = sys.argv[1]; steps = int(sys.argv[2]) if len(sys.argv) > 2 else 128
D = int(sys.argv[3]) if len(sys.argv) > 3 else 512; NL = int(sys.argv[4]) if len(sys.argv) > 4 else 16
FF = int(sys.argv[5]) if len(sys.argv) > 5 else 2048; H = int(sys.argv[6]) if len(sys.argv) > 6 else 4
V = int(sys.argv[7]) if len(sys.argv) > 7 else 8000
os.makedirs(out, exist_ok=True); rng = np.random.default_rng(1)
tensors = []  # (name, array)
def add(n, a): tensors.append((n, np.asarray(a, np.float32)))
add("tok", rng.normal(0, 0.02, (V, D))); add("pos", rng.normal(0, 0.02, (steps, D)))
for l in range(NL):
    g = "L%d." % l
    for n in ("ln1g", "ln2g"): add(g + n, np.ones(D))
    for n in ("ln1b", "ln2b"): add(g + n, np.zeros(D))
    for n in "qkv": add(g + "w" + n, rng.normal(0, 0.02, (D, D))); add(g + "b" + n, np.zeros(D))
    add(g + "wo", rng.normal(0, 0.02, (D, D))); add(g + "bo", np.zeros(D))
    add(g + "w1", rng.normal(0, 0.02, (D, FF))); add(g + "b1", np.zeros(FF))
    add(g + "w2", rng.normal(0, 0.02, (FF, D))); add(g + "b2", np.zeros(D))
add("lnfg", np.ones(D)); add("lnfb", np.zeros(D)); add("headw", rng.normal(0, 0.02, (D, V))); add("headb", np.zeros(V))
off = 0; man = []
with open(os.path.join(out, "tensors.bin"), "wb") as f:
    for n, a in tensors:
        a.tofile(f); man.append("%s %d %d %s" % (n, off, a.ndim, " ".join(str(x) for x in a.shape))); off += a.size
open(os.path.join(out, "manifest.txt"), "w").write("\n".join(man) + "\n")
prog = []
for l in range(NL):
    for n in ("wq", "wk", "wv", "wo", "w1", "w2"): prog.append("W L%d.%s %d" % (l, n, l + 1))
prog += ["W headw %d" % (NL + 1), "W tok 0", "W pos 0"]
prog += ["GATHER x0 tok tokid 0 #emb", "GATHER p0 pos posn 0 #emb", "ADD x x0 p0 #emb"]
for l in range(NL):
    t = l + 1; g = "L%d." % l
    prog += ["LN h x %sln1g %sln1b #L%d.attn" % (g, g, l)]
    for n in "qkv": prog.append("MM %s h %sw%s %sb%s %d #L%d.attn" % (n, g, n, g, n, t, l))
    prog += ["KVAPP kc%d k %d #L%d.attn" % (l, t, l), "KVAPP vc%d v %d #L%d.attn" % (l, t, l), "ATTNC a q kc%d vc%d %d %d #L%d.attn" % (l, l, H, t, l), "MM o a %swo %sbo %d #L%d.attn" % (g, g, t, l), "ADD x x o #L%d.attn" % l,
             "LN h x %sln2g %sln2b #L%d.mlp" % (g, g, l), "MM u h %sw1 %sb1 %d #L%d.mlp" % (g, g, t, l), "GELU u u #L%d.mlp" % l, "MM dn u %sw2 %sb2 %d #L%d.mlp" % (g, g, t, l), "ADD x x dn #L%d.mlp" % l]
prog += ["LN x x lnfg lnfb #head", "MM logits x headw headb %d #head" % (NL + 1)]
open(os.path.join(out, "program.txt"), "w").write("\n".join(prog) + "\n")
rng.integers(0, V, steps).astype(np.float32).tofile(os.path.join(out, "inputs.bin")); open(os.path.join(out, "input.txt"), "w").write("tokid 1\n")
print("written", out, "params", sum(a.size for _, a in tensors))
