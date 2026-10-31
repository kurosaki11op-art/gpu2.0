#!/usr/bin/env python3
"""Confidence-gated cascade of a small and a large language model (31 Oct 2026). Test plan and pre-set bars: new_start/step8_cascade_lm_plan.md (written before any run).

Stage A (teacher-forced, held-out text): per-token log-probabilities of both models on the same text, then the cascade 'use the small model unless its margin (top-1 minus top-2
probability) is low, then use the large model' at escalation fractions 5%..100%, against random gating and an oracle, with the weight-bytes cost per token.
Stage B (live greedy generation with a real cascade): the small model decodes every token; on a low-margin step the large model catches up on the tokens it has not seen (one batched
pass over the gap, KV cache kept) and its prediction is used. Measures tokens/s, joules per token (NVML power sampling; only valid on an otherwise idle GPU) and agreement with the large model.

Usage:  python cascade_lm_test.py --small NAME_OR_PATH --big NAME_OR_PATH [--text file.txt] [--device cuda] [--big-4bit] [--stage both|A|B] [--out results.json]
Both models must share one tokenizer (same family). Needs: torch, transformers, numpy; optional: datasets (default text), nvidia-ml-py (energy), bitsandbytes (--big-4bit).
"""
import argparse, json, threading, time
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_text(a):
    if a.text:
        return open(a.text, encoding="utf-8", errors="ignore").read()
    from datasets import load_dataset
    return "\n\n".join(load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")["text"])

def load_model(name, device, four_bit=False):
    kw = {}
    if four_bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16)
        kw["device_map"] = {"": 0}
    else:
        kw["dtype"] = torch.float16 if device == "cuda" else torch.float32
    m = AutoModelForCausalLM.from_pretrained(name, **kw)
    if not four_bit:
        m = m.to(device)
    return m.eval()

@torch.no_grad()
def teacher_forced(model, ids, win, device):
    """per-position stats over windows: log-prob of the true next token, and margin (top1 - top2 prob) of the model."""
    lp, mg = [], []
    for i in range(0, ids.numel() - win, win):
        x = ids[i:i + win].unsqueeze(0).to(device)
        logits = model(x[:, :-1]).logits[0].float()
        p = torch.log_softmax(logits, -1)
        lp.append(p.gather(1, x[0, 1:].unsqueeze(1)).squeeze(1).cpu())
        t2 = p.exp().topk(2, dim=-1).values
        mg.append((t2[:, 0] - t2[:, 1]).cpu())
    return torch.cat(lp).numpy(), torch.cat(mg).numpy()

def stage_a(small, big, ids, win, device):
    lp_s, mg_s = teacher_forced(small, ids, win, device)
    lp_b, _ = teacher_forced(big, ids, win, device)
    n = lp_s.size; nll_s, nll_b = -lp_s.mean(), -lp_b.mean()
    ws, wb = small.get_memory_footprint(), big.get_memory_footprint()
    rng = np.random.default_rng(0); order = np.argsort(mg_s); gain = np.argsort(-(lp_b - lp_s))
    rows = []
    for r in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0]:
        k = int(round(r * n)); esc = np.zeros(n, bool); esc[order[:k]] = True
        casc = -np.where(esc, lp_b, lp_s).mean()
        rnd = np.mean([-np.where(np.isin(np.arange(n), rng.choice(n, k, replace=False)), lp_b, lp_s).mean() for _ in range(5)])
        orc = np.zeros(n, bool); orc[gain[:k]] = True; orc_nll = -np.where(orc, lp_b, lp_s).mean()
        den = max(nll_s - nll_b, 1e-9)
        rows.append(dict(r=r, tau=float(mg_s[order[min(k, n) - 1]]), nll=float(casc), ratio_to_big=float(casc / nll_b), gap_closed=float((nll_s - casc) / den),
                         gap_closed_random=float((nll_s - rnd) / den), gap_closed_oracle=float((nll_s - orc_nll) / den), bytes_ratio=float((ws + r * wb) / wb)))
    return dict(tokens=int(n), nll_small=float(nll_s), nll_big=float(nll_b), bytes_small=ws, bytes_big=wb, rows=rows)

class Power:
    """NVML power sampler (watts at ~20 Hz); energy = integral. Returns None if NVML is unavailable."""
    def __init__(self):
        try:
            import pynvml; pynvml.nvmlInit(); self.h = pynvml.nvmlDeviceGetHandleByIndex(0); self.nv = pynvml
        except Exception:
            self.nv = None
    def idle(self, s=8.0):
        if not self.nv: return None
        w = []; t = time.time()
        while time.time() - t < s: w.append(self.nv.nvmlDeviceGetPowerUsage(self.h) / 1000.0); time.sleep(0.05)
        return float(np.mean(w))
    def start(self):
        self.s = []; self.stop_f = False
        if not self.nv: return
        def run():
            while not self.stop_f: self.s.append((time.time(), self.nv.nvmlDeviceGetPowerUsage(self.h) / 1000.0)); time.sleep(0.05)
        self.th = threading.Thread(target=run, daemon=True); self.th.start()
    def stop(self):
        self.stop_f = True
        if not self.nv: return None
        self.th.join(); t = np.array([x[0] for x in self.s]); w = np.array([x[1] for x in self.s])
        return float(np.sum((w[1:] + w[:-1]) / 2 * np.diff(t))) if t.size > 1 else None

@torch.no_grad()
def generate(small, big, prompt, n_new, tau, device, mode):
    """greedy generation. mode: 'big' (large alone), 'small' (small alone), 'cascade' (escalate when small margin < tau). returns tokens, number of big passes."""
    seq = prompt.tolist(); sc = bc = None; big_len = 0; passes = 0
    s_in = torch.tensor([seq], device=device)
    for _ in range(n_new):
        if mode == "big":
            o = big(torch.tensor([seq[big_len:]], device=device), past_key_values=bc, use_cache=True); bc = o.past_key_values; big_len = len(seq); passes += 1
            nxt = int(o.logits[0, -1].argmax()); seq.append(nxt); continue
        o = small(s_in, past_key_values=sc, use_cache=True); sc = o.past_key_values
        pr = torch.softmax(o.logits[0, -1].float(), -1); t2 = pr.topk(2).values; nxt = int(pr.argmax())
        if mode == "cascade" and float(t2[0] - t2[1]) < tau:
            ob = big(torch.tensor([seq[big_len:]], device=device), past_key_values=bc, use_cache=True); bc = ob.past_key_values; big_len = len(seq); passes += 1
            nxt = int(ob.logits[0, -1].argmax())
        seq.append(nxt); s_in = torch.tensor([[nxt]], device=device)
    return seq[len(prompt):], passes

@torch.no_grad()
def agreement(big, prompt, gen, device):
    full = torch.tensor([prompt.tolist() + gen], device=device); lg = big(full).logits[0].float()
    pred = lg[len(prompt) - 1:-1].argmax(-1).cpu().numpy(); lp = torch.log_softmax(lg[len(prompt) - 1:-1], -1)
    nll = -lp.gather(1, torch.tensor(gen, device=device).unsqueeze(1)).mean().item()
    return float((pred == np.array(gen)).mean()), nll

def stage_b(small, big, ids, taus, device, n_prompts, plen, n_new):
    pw = Power(); idle = pw.idle(); res = dict(idle_power_w=idle, runs=[])
    stride = max(1, (ids.numel() - plen - 1) // n_prompts); prompts = [ids[i * stride:i * stride + plen] for i in range(n_prompts)]
    configs = [("big alone", "big", 0.0), ("small alone", "small", 0.0)] + [(f"cascade r~{r:.2f}", "cascade", t) for r, t in taus]
    generate(small, big, prompts[0], 8, 0.5, device, "cascade")  # warm-up
    for name, mode, tau in configs:
        pw.start(); t0 = time.time(); agr, nll, passes, toks = [], [], 0, 0
        gens = []
        for p in prompts:
            g, ps = generate(small, big, p, n_new, tau, device, mode); passes += ps; toks += len(g); gens.append((p, g))
        if device == "cuda": torch.cuda.synchronize()
        dt = time.time() - t0; e = pw.stop()
        for p, g in gens:
            a, n_ = agreement(big, p, g, device); agr.append(a); nll.append(n_)
        res["runs"].append(dict(name=name, tokens_per_s=toks / dt, joules_per_token=(e / toks if e else None), joules_per_token_idle_subtracted=((e - idle * dt) / toks if e and idle else None),
                                big_passes_per_token=passes / toks, agreement_with_big=float(np.mean(agr)), nll_under_big=float(np.mean(nll))))
        print(res["runs"][-1])
    return res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--small", required=True); ap.add_argument("--big", required=True); ap.add_argument("--text"); ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--big-4bit", action="store_true"); ap.add_argument("--stage", default="both"); ap.add_argument("--windows", type=int, default=40); ap.add_argument("--win", type=int, default=512)
    ap.add_argument("--prompts", type=int, default=12); ap.add_argument("--plen", type=int, default=48); ap.add_argument("--new", type=int, default=160); ap.add_argument("--out", default="cascade_lm_results.json")
    a = ap.parse_args(); tok = AutoTokenizer.from_pretrained(a.small)
    assert tok.get_vocab() == AutoTokenizer.from_pretrained(a.big).get_vocab(), "the two models must share a tokenizer"
    ids = tok(load_text(a), return_tensors="pt").input_ids[0][: a.windows * a.win + 1]
    small, big = load_model(a.small, a.device), load_model(a.big, a.device, a.big_4bit); out = {}
    if a.stage in ("A", "both"):
        out["A"] = stage_a(small, big, ids, a.win, a.device); A = out["A"]
        print(f"tokens {A['tokens']}  nll small {A['nll_small']:.4f}  big {A['nll_big']:.4f}  weight bytes small {A['bytes_small']/1e9:.2f} GB big {A['bytes_big']/1e9:.2f} GB")
        print(f"{'esc':>5} {'tau':>8} {'nll':>8} {'x big':>7} {'gap closed':>11} {'random':>8} {'oracle':>8} {'bytes/big':>10}")
        for r in A["rows"]: print(f"{r['r']:>5.2f} {r['tau']:>8.4f} {r['nll']:>8.4f} {r['ratio_to_big']:>7.3f} {r['gap_closed']:>11.3f} {r['gap_closed_random']:>8.3f} {r['gap_closed_oracle']:>8.3f} {r['bytes_ratio']:>10.3f}")
    if a.stage in ("B", "both"):
        taus = [(r["r"], r["tau"]) for r in out["A"]["rows"] if r["r"] in (0.10, 0.20, 0.30)] if "A" in out else [(0.2, 0.3)]
        out["B"] = stage_b(small, big, ids, taus, a.device, a.prompts, a.plen, a.new)
    json.dump(out, open(a.out, "w"), indent=1); print("wrote", a.out)

if __name__ == "__main__":
    main()
