#!/usr/bin/env python3
"""E1 check: the Rust engine's logits against PyTorch on 16 fixed prompts. usage: python check_e1.py MODEL_ID WORKDIR  (needs /tmp/engine built from engine.rs)
Prints max absolute error over all positions and the greedy-token agreement; bar (engine_plan.md): max abs error <= 1e-3 and 100% agreement."""
import sys, subprocess, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download
import glob, os, json
mid, work = sys.argv[1], sys.argv[2]; os.makedirs(work, exist_ok=True)
tok = AutoTokenizer.from_pretrained(mid); model = AutoModelForCausalLM.from_pretrained(mid, dtype=torch.float32).eval()
texts = ["The quick brown fox jumps over the lazy dog.", "In 1969, humans first landed on the Moon.", "def add(a, b):\n    return a + b", "Rust is a systems programming language focused on safety.", "Water boils at 100 degrees Celsius at sea level.",
         "The capital of France is Paris, and the capital of Italy is Rome.", "She opened the door and saw nothing but darkness.", "A GPU runs thousands of threads in parallel.", "Once upon a time there was a small robot.", "To be, or not to be, that is the question.",
         "Machine learning models are trained on large datasets.", "The stock market closed higher on Friday.", "import numpy as np\nx = np.zeros(10)", "Bananas are rich in potassium and fibre.", "He said he would call, but the phone never rang.", "Photosynthesis converts light into chemical energy."]
ids = [tok(t)["input_ids"] for t in texts]; open(f"{work}/ids.txt", "w").write("\n".join(" ".join(map(str, s)) for s in ids) + "\n")
nh = model.config.n_head; mp = glob.glob(snapshot_download(mid, allow_patterns=["*.safetensors"]) + "/*.safetensors")[0]
subprocess.check_call(["/tmp/engine", mp, str(nh), f"{work}/ids.txt", f"{work}/out.bin"])
out = np.fromfile(f"{work}/out.bin", dtype=np.float32); V = model.config.vocab_size; pos = 0; maxerr = 0.0; agree = 0; total = 0
with torch.no_grad():
    for s in ids:
        ref = model(torch.tensor([s])).logits[0].numpy(); mine = out[pos:pos + len(s) * V].reshape(len(s), V); pos += len(s) * V
        maxerr = max(maxerr, float(np.abs(ref - mine).max())); agree += int((ref.argmax(1) == mine.argmax(1)).sum()); total += len(s)
print(f"{mid}: {len(ids)} prompts, {total} positions, max abs logit error {maxerr:.2e}, greedy-token agreement {agree}/{total}")
print("E1 bar (error <= 1e-3 and full agreement):", "PASS" if maxerr <= 1e-3 and agree == total else "FAIL")
