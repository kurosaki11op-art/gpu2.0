"""Draft mode, round 3: new drafters, measured as whole tokens per GPU pass (lossless greedy speculative decoding).
GPU stand-in: our byte-level nanoGPT (out_big) greedy continuation at word-piece boundaries (same protocol as the
real-model test local_llm_test2.py). Drafters:
  spark  : SPARK v2 autoregressive draft (as in the 9B test)
  copy   : copy-drafting -- find the latest earlier occurrence of the last N bytes in the text seen so far and copy
           what followed (hardware analogue: recall entries store a pointer into a history ring buffer)
  multi  : best of several drafts verified in one pass (tree verification): spark, copy, and SPARK branches started
           from each alternative candidate its recall memories offer for the first byte
Reports tokens per GPU pass = whole GPU tokens covered by the accepted draft + 1."""
import copy, json, os, re, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
from model import GPT, GPTConfig  # noqa
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
text = bytes(Z["test_text"]); s = text.decode("latin-1")
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
L = 40


def pieces(b):
    return [x.group(0).encode("latin-1") for x in PRETOK.finditer(b.decode("latin-1"))]


def gpu_cont(i):
    seq = list(text[max(0, i - 127):i + 1])
    with torch.no_grad():
        for _ in range(L):
            lg, _ = m(torch.tensor(seq[-128:])[None]); seq.append(int(lg[0, -1].argmax()))
    return bytes(seq[-L:])


def spark_draft(h, first, n=L):
    d = [first]
    for _ in range(n - 1):
        o = h.step(int(d[-1])); d.append(o["pred"])
    return bytes(d)


def copy_draft(i, N):
    ctx = text[i - N + 1:i + 1]
    j = text.rfind(ctx, 0, i)                 # latest earlier occurrence (hardware: pointer stored in recall entry)
    if j < 0:
        return b""
    return text[j + N:j + N + L]


def copy_longest(i, nmax=32, nmin=3):
    for N in range(nmax, nmin - 1, -1):
        d = copy_draft(i, N)
        if d:
            return d
    return b""


def accepted(draft, gpu):
    acc, pos = 0, 0
    for p in pieces(gpu):
        if draft[pos:pos + len(p)] == p:
            acc += 1; pos += len(p)
        else:
            break
    return acc + 1


ends = sorted(x.end() - 1 for x in PRETOK.finditer(s))
cand = [e for e in ends if 1500 <= e < len(text) - 60]
pts = set(cand[int(k)] for k in np.linspace(0, len(cand) - 1, 400))
g = g2.GoldenV2(W, cfg, tb=12, lut=lut); res = {k: [] for k in ("spark", "copy6", "copy4", "copyL", "copy+spark", "multi")}
for i, b in enumerate(text):
    o = g.step(int(b))
    if i in pts:
        gp = gpu_cont(i)
        sd = spark_draft(copy.deepcopy(g), o["pred"])
        alts = [v for v in dict.fromkeys(g.last_alts) if v != o["pred"]][:2]
        branches = [sd] + [spark_draft(copy.deepcopy(g), v) for v in alts]
        c6, c4 = copy_draft(i, 6), copy_draft(i, 4)
        res["spark"].append(accepted(sd, gp))
        res["copy6"].append(accepted(c6, gp) if c6 else 1)
        res["copy4"].append(accepted(c4, gp) if c4 else 1)
        cL = copy_longest(i)
        res["copyL"].append(accepted(cL, gp) if cL else 1)
        res["copy+spark"].append(max(accepted(sd, gp), accepted(cL, gp) if cL else 1))
        res["multi"].append(max([accepted(x, gp) for x in branches + [c6, c4, cL] if x] or [1]))
print(f"{len(pts)} points, GPU stand-in = byte-level nanoGPT, tokens per GPU pass (GPU alone = 1.00):")
for k, v in res.items():
    print(f"  {k:11s}: {np.mean(v):.2f}")
json.dump({k: float(np.mean(v)) for k, v in res.items()}, open(os.path.join(HERE, "..", "results", "draft_v3_local.json"), "w"), indent=1)
