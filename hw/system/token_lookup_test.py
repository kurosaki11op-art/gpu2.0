#!/usr/bin/env python3
"""Token-level test of lookup drafting on a REAL model (not bytes): how many tokens does the big model's greedy output
accept per target pass when drafts come from (a) prompt lookup (longest earlier n-gram match) or (b) SPARK-L style hashed
tables (CRC-32 hash, orders 1-4, 2-bit hysteresis counters) learned online from the prompt and the tokens committed so far?
Greedy verification is lossless, so acceptance can be computed offline from the model's own greedy transcript:
a pass drafts up to K tokens, the longest prefix equal to the real continuation is accepted, plus one bonus token from the
verifying pass: MAT = committed tokens / passes (the unit used by published speculative-decoding work; plain decoding = 1.0).
Tests code (Python source from the trace) and prose (public-domain book slices, hw/system/data/prose_slices.txt).
Needs: torch, transformers (GPU optional).  Run:  py -3.12 hw\\system\\token_lookup_test.py --model Qwen/Qwen2.5-Coder-1.5B --n 20 --gen 128
Plumbing test with a random tiny model (numbers meaningless):  python hw/system/token_lookup_test.py --tiny"""
import argparse, base64, json, os, zlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ORDERS = (1, 2, 3, 4); TB = 12


class TokTable:
    def __init__(self):
        self.t = [dict() for _ in ORDERS]

    @staticmethod
    def key(hist, k, o):
        v = zlib.crc32(b"".join(int(x).to_bytes(4, "little") for x in hist[-o:]), k + 1) & 0xFFFFFFFF
        return v >> (32 - TB), (v >> 4) & 0xFFF

    def update(self, hist, tok):                       # hist = tokens before tok
        for k, o in enumerate(ORDERS):
            if len(hist) < o: continue
            s, tag = self.key(hist, k, o); e = self.t[k].get(s)
            if e and e[0] == tag:
                if e[1] == tok: e[2] = min(e[2] + 1, 3)
                elif e[2] > 0: e[2] -= 1
                else: e[1] = tok
            else: self.t[k][s] = [tag, tok, 0]

    def draft(self, hist, K):
        h = list(hist); out = []
        for _ in range(K):
            nxt = None
            for k in reversed(range(len(ORDERS))):
                o = ORDERS[k]
                if len(h) < o: continue
                s, tag = self.key(h, k, o); e = self.t[k].get(s)
                if e and e[0] == tag: nxt = e[1]; break
            if nxt is None: break
            out.append(nxt); h.append(nxt)
        return out


def pld_draft(hist, K, nmax=3):
    for n in range(min(nmax, len(hist) - 1), 0, -1):
        key = hist[-n:]
        for j in range(len(hist) - n - 1, -1, -1):     # latest earlier occurrence
            if hist[j:j + n] == key: return hist[j + n:j + n + K]
    return []


def repetition(ctx, gen, n=3):
    """share of generated tokens that an earlier n-gram in prompt+generated text would have predicted exactly (how copyable the output is)"""
    seen = {}; full = ctx + gen; hits = 0
    for i in range(n, len(full)):
        key = tuple(full[i - n:i])
        if i >= len(ctx) and seen.get(key) == full[i]: hits += 1
        seen[key] = full[i]
    return hits / max(1, len(gen))


def simulate(ctx, gen, K, mode):
    tab = TokTable(); hist = []
    for t in ctx:
        tab.update(hist, t); hist.append(t)
    pos = passes = 0
    while pos < len(gen):
        if mode == "pld": d = pld_draft(hist, K)
        elif mode == "table": d = tab.draft(hist, K)
        else:                                          # both drafts verified in one pass (a two-branch tree): keep the longer match
            a, b = pld_draft(hist, K), tab.draft(hist, K)
            def m(dd): return next((i for i in range(min(len(dd), len(gen) - pos)) if dd[i] != gen[pos + i]), min(len(dd), len(gen) - pos))
            d = a if m(a) >= m(b) else b
        acc = 0
        while acc < len(d) and pos + acc < len(gen) and d[acc] == gen[pos + acc]: acc += 1
        take = min(acc + 1, len(gen) - pos); passes += 1
        for tok in gen[pos:pos + take]:
            tab.update(hist, tok); hist.append(tok)
        pos += take
    return len(gen) / passes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B")
    ap.add_argument("--n", type=int, default=20); ap.add_argument("--gen", type=int, default=128)
    ap.add_argument("--ctx", type=int, default=1500, help="prompt characters"); ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--tiny", action="store_true")
    ap.add_argument("--chat", action="store_true", help="instruct model: wrap each excerpt in a chat request to continue it")
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    code = base64.b64decode(json.load(open(os.path.join(HERE, "data", "spark_trace.json")))["text_b64"]).decode("latin-1")
    prose = open(os.path.join(HERE, "data", "prose_slices.txt"), encoding="latin-1").read()
    sets = {"code": [code[i:i + a.ctx] for i in np.linspace(2000, len(code) - a.ctx - 1, a.n).astype(int)],
            "prose": [prose[i:i + a.ctx] for i in np.linspace(0, len(prose) - a.ctx - 1, a.n).astype(int)]}
    if a.tiny:
        from transformers import Qwen2Config, Qwen2ForCausalLM
        model = Qwen2ForCausalLM(Qwen2Config(vocab_size=1000, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                                             num_attention_heads=4, num_key_value_heads=2)).eval(); tok = None
    else:
        tok = AutoTokenizer.from_pretrained(a.model)
        dt = torch.float16 if dev == "cuda" else torch.float32
        try:
            model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dt)
        except TypeError:                                  # older transformers
            model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=dt)
        model = model.to(dev).eval()
        print(f"model {a.model} on {dev} ({dt}); if this is far below ~20 tokens/s the model does not fit in GPU memory: try a smaller one", flush=True)
    import time
    res = {}
    for name, prompts in sets.items():
        acc = {"pld": [], "table": [], "both": []}; rep = []
        for p in prompts:
            if tok is None:
                ids = torch.randint(0, 1000, (1, 200))
            elif a.chat:
                ids = tok.apply_chat_template([{"role": "user", "content": "Continue this text in the same style:\n\n" + p}],
                                              add_generation_prompt=True, return_tensors="pt")
            else:
                ids = tok(p, return_tensors="pt").input_ids
            t0 = time.time()
            with torch.no_grad():
                out = model.generate(ids.to(dev), max_new_tokens=a.gen, min_new_tokens=a.gen, do_sample=False)
            if len(acc["pld"]) == 0:
                print(f"  first {name} prompt: {ids.shape[1]} prompt tokens, {a.gen / (time.time() - t0):.1f} generated tokens/s", flush=True)
            ctx, gen = ids[0].tolist(), out[0, ids.shape[1]:].tolist()
            for mode in acc: acc[mode].append(simulate(ctx, gen, a.k, mode))
            rep.append(repetition(ctx, gen))
        res[name] = {m: float(np.mean(v)) for m, v in acc.items()}; res[name]["copyable_share"] = float(np.mean(rep))
        print(f"{name:5s} (K={a.k}, {len(prompts)} prompts x {a.gen} tokens)  tokens per target pass:  "
              f"prompt-lookup {res[name]['pld']:.2f} | hash tables {res[name]['table']:.2f} | both {res[name]['both']:.2f} | "
              f"copyable output {res[name]['copyable_share']:.0%}", flush=True)
    json.dump({"model": "tiny-random" if a.tiny else a.model, "k": a.k, "result": res},
              open(os.path.join(HERE, "..", "results", "token_lookup_%s%s.json" % ("tiny" if a.tiny else a.model.replace("/", "_"), "_chat" if a.chat else "")), "w"), indent=1)
    print("saved hw/results/token_lookup_%s.json (send it, or paste the two lines above)" % ("tiny" if a.tiny else a.model.replace("/", "_")))


if __name__ == "__main__":
    main()
