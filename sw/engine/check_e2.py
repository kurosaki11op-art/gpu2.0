#!/usr/bin/env python3
"""E2 check: INT8 weight-only quantisation against our own fp32 pass. usage: python check_e2.py WORKDIR   (needs /tmp/engine built from engine.rs; model distilgpt2)
Bars (engine_plan.md): loss increase <= 0.01 nats per token on >= 64 windows with a paired interval; INT8 weight bytes <= 0.3 x fp32; speed reported against the prediction P3 in engine_study.md."""
import sys, os, glob, subprocess, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
work = sys.argv[1]; os.makedirs(work, exist_ok=True); mid = "distilgpt2"
tok = AutoTokenizer.from_pretrained(mid); model = AutoModelForCausalLM.from_pretrained(mid, dtype=torch.float32).eval()
root = os.path.dirname(os.path.abspath(__file__)) + "/../../"
text = "\n".join(open(root + f, encoding="utf-8").read() for f in ["docs/PROJECT_MEMORY.md", "docs/own_gpu_charter.md", "docs/product_finish_plan.md"])
ids = tok(text)["input_ids"]; W = 65; wins = [ids[i:i + W] for i in range(0, len(ids) - W, W)][:96]
open(f"{work}/win.txt", "w").write("\n".join(" ".join(map(str, w)) for w in wins) + "\n")
mp = glob.glob(os.path.expanduser("~/.cache/huggingface/hub/models--distilgpt2/snapshots/*/model.safetensors"))[0]
def run(mode, inp, out): 
    r = subprocess.run(["/tmp/engine", mp, "12", inp, out, mode], capture_output=True, text=True); return r.stderr
e32 = run("loss", f"{work}/win.txt", f"{work}/l32.txt"); e8 = run("loss_q", f"{work}/win.txt", f"{work}/l8.txt")
l32 = np.loadtxt(f"{work}/l32.txt"); l8 = np.loadtxt(f"{work}/l8.txt")
with torch.no_grad():
    ref = np.array([torch.nn.functional.cross_entropy(model(torch.tensor([w[:-1]])).logits[0], torch.tensor(w[1:])).item() for w in wins[:8]])
print(f"windows {len(wins)} x {W - 1} predictions; engine fp32 vs PyTorch loss on 8 windows: max difference {np.abs(ref - l32[:8]).max():.2e} nats")
d = l8 - l32; se = d.std(ddof=1) / np.sqrt(len(d)); print(f"mean loss fp32 {l32.mean():.4f}, INT8 {l8.mean():.4f}; paired increase {d.mean():+.5f} nats per token, 95% interval [{d.mean() - 1.96 * se:+.5f}, {d.mean() + 1.96 * se:+.5f}]")
print("E2 quality bar (increase <= 0.01, upper end of the interval): ", "PASS" if d.mean() + 1.96 * se <= 0.01 else "FAIL")
print([l for l in e8.splitlines() if "weights read" in l][0])
