#!/usr/bin/env python3
"""End-to-end wall-clock test: plain greedy decoding vs software prompt-lookup speculative decoding, on a real GPU.
Not tested on a GPU by the author (written in a CPU-only container): run it, and send back the output.

Needs: pip install torch (CUDA build) transformers   -- and the model downloads from Hugging Face on first run.
Run:   py -3.12 hw\\system\\real_speed_test.py --model Qwen/Qwen2.5-Coder-3B --n 20 --new 128

Reports, per mode: tokens per second, joules per token (GPU telemetry only, nvidia-smi), and whether the outputs are
identical (greedy lookup decoding must be lossless). This is the baseline SPARK hardware has to beat."""
import argparse, base64, json, os, shutil, subprocess, threading, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


class Power:
    def __init__(self):
        self.ok = shutil.which("nvidia-smi") is not None; self.s = []; self.run = False

    def _loop(self):
        while self.run:
            try:
                out = subprocess.run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True, timeout=5).stdout.split()[0]
                self.s.append(float(out))
            except Exception:
                pass
            time.sleep(0.1)

    def start(self):
        self.s = []; self.run = True
        if self.ok:
            self.t = threading.Thread(target=self._loop, daemon=True); self.t.start()

    def stop(self):
        self.run = False
        if self.ok:
            self.t.join()
        return float(np.mean(self.s)) if self.s else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-3B")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--new", type=int, default=128)
    ap.add_argument("--ctx", type=int, default=800)
    ap.add_argument("--lookup", type=int, default=10, help="prompt_lookup_num_tokens")
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16).cuda().eval()
    text = base64.b64decode(json.load(open(os.path.join(HERE, "data", "spark_trace.json")))["text_b64"]).decode("latin-1")
    pts = np.linspace(2000, len(text) - 400, a.n).astype(int)
    prompts = [text[i - a.ctx:i] for i in pts]
    for mode in ("plain", "lookup", "plain", "lookup"):          # first pair warms up the kernels; second pair is reported
        kw = {} if mode == "plain" else {"prompt_lookup_num_tokens": a.lookup}
        outs, ntok = [], 0
        torch.cuda.synchronize(); pw = Power(); pw.start(); t0 = time.time()
        for p in prompts:
            ids = tok(p, return_tensors="pt").to("cuda")
            with torch.no_grad():
                o = model.generate(**ids, max_new_tokens=a.new, do_sample=False, **kw)
            new = o[0, ids["input_ids"].shape[1]:]; outs.append(new.tolist()); ntok += len(new)
        torch.cuda.synchronize(); dt = time.time() - t0; w = pw.stop()
        print(f"{mode:7s}: {ntok / dt:6.1f} tokens/s" + (f", {w:.0f} W -> {w * dt / ntok:.3f} J/token (GPU telemetry only)" if w else ""))
        if mode == "plain":
            ref = outs
        elif ref is not None:
            same = np.mean([x == y for x, y in zip(ref, outs)]); print(f"         outputs identical to plain: {same:.0%}")


if __name__ == "__main__":
    ref = None
    main()
