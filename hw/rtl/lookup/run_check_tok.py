#!/usr/bin/env python3
"""spark_lookup_tok.v vs TokCore (bit-exact): every drafted token, its source order and counter, and the draft length, at every
position of word-level token streams (code and prose), with token IDs above 2^16 to exercise all 18 bits.
Also checks that TokCore drafts the same tokens as the table drafter measured by token_lookup_test.py.
usage: python run_check_tok.py"""
import os, re, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "system"))
from lookup_tok_ref import TokCore  # noqa
import token_lookup_test as tlt  # noqa
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
Z = np.load(os.path.join(HERE, "..", "..", "system", "out", "slice_cache.npz"))
code = bytes(Z["test_text"]).decode("latin-1")
prose = open(os.path.join(HERE, "..", "..", "system", "data", "prose_slices.txt"), encoding="latin-1").read()
N, K = 1500, 8
ok = True
for name, text in (("code", code), ("prose", prose)):
    vocab = {}; toks = []
    for m in PRETOK.finditer(text):
        toks.append(vocab.setdefault(m.group(0), 100000 + len(vocab)))
        if len(toks) == N: break
    for tb in (11, 12):
        open(os.path.join(HERE, "in_tok.hex"), "w").write("\n".join("%05x" % t for t in toks) + "\n")
        subprocess.run(["iverilog", "-g2005", "-o", "/tmp/lkt.vvp", f"-Ptb_spark_lookup_tok.TB={tb}", f"-Ptb_spark_lookup_tok.N={N}",
                        f"-Ptb_spark_lookup_tok.K={K}", "spark_lookup_tok.v", "tb_spark_lookup_tok.v"], cwd=HERE, check=True)
        out = subprocess.run(["vvp", "-n", "/tmp/lkt.vvp"], cwd=HERE, capture_output=True, text=True).stdout
        cyc = [l for l in out.splitlines() if l.startswith("DONE")][0]
        core = TokCore(tb); tlt.TB = tb; tt = tlt.TokTable(); hist = []
        bad = same_as_measured = 0; drafted = 0
        for i, line in enumerate(open(os.path.join(HERE, "out_tok.txt"))):
            body, n = line.split("|"); f = body.split()
            got = [(int(f[x], 16), int(f[x + 1]), int(f[x + 2])) for x in range(0, len(f), 3)]
            exp = core.draft(K)
            if got != exp or int(n) != len(exp):
                bad += 1
                if bad <= 3: print("MISMATCH", name, tb, i, got, exp)
            same_as_measured += [g[0] for g in exp] == tt.draft(hist, K); drafted += len(got)
            core.learn(toks[i]); tt.update(hist, toks[i]); hist.append(toks[i])
        print(f"{name:5s} TB={tb}: {N} positions, mismatches {bad}, reference = measured drafter at {same_as_measured}/{N} positions, "
              f"{drafted / N:.2f} tokens proposed per draft  [{cyc}]")
        ok &= bad == 0 and same_as_measured == N
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
