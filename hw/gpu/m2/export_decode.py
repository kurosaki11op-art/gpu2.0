#!/usr/bin/env python3
"""M2: builds the decode program (one token per step, key-value cache on the tile) for the M1 transformer from the same tensors. usage: python export_decode.py WORKDIR  (WORKDIR from export_models.py; writes WORKDIR/lm_dec)"""
import os, shutil, sys
import numpy as np
W = sys.argv[1]; src = os.path.join(W, "lm"); d = os.path.join(W, "lm_dec"); os.makedirs(d, exist_ok=True); NL, H = 2, 4
for f in ("tensors.bin", "manifest.txt"): shutil.copy(os.path.join(src, f), os.path.join(d, f))
base = [l for l in open(os.path.join(src, "program.txt")).read().splitlines() if l.startswith("W ")]
prog = ["GATHER x0 tok tokid 0 #emb", "GATHER p0 pos posn 0 #emb", "ADD x x0 p0 #emb"]
for l in range(NL):
    t = l + 1; g = "L%d." % l
    prog += ["LN h x %sln1g %sln1b #L%d.attn" % (g, g, l)]
    for n in "qkv": prog.append("MM %s h %sw%s %sb%s %d #L%d.attn" % (n, g, n, g, n, t, l))
    prog += ["KVAPP kc%d k %d #L%d.attn" % (l, t, l), "KVAPP vc%d v %d #L%d.attn" % (l, t, l), "ATTNC a q kc%d vc%d %d %d #L%d.attn" % (l, l, H, t, l), "MM o a %swo %sbo %d #L%d.attn" % (g, g, t, l), "ADD x x o #L%d.attn" % l,
             "LN h x %sln2g %sln2b #L%d.mlp" % (g, g, l), "MM u h %sw1 %sb1 %d #L%d.mlp" % (g, g, t, l), "GELU u u #L%d.mlp" % l, "MM dn u %sw2 %sb2 %d #L%d.mlp" % (g, g, t, l), "ADD x x dn #L%d.mlp" % l]
prog += ["LN x x lnfg lnfb #head", "MM logits x headw headb %d #head" % (NL + 1)]
open(os.path.join(d, "program.txt"), "w").write("\n".join(base + prog) + "\n")
ids = np.fromfile(os.path.join(src, "inputs.bin"), np.float32)[:64]; ids.tofile(os.path.join(d, "inputs.bin")); open(os.path.join(d, "input.txt"), "w").write("tokid 1\n"); print("decode program written; 64 steps from the first evaluation window")
