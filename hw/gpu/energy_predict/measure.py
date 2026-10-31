#!/usr/bin/env python3
"""Energy-per-token measurement for one machine (wedge 1, test G1). Run this on the machine being measured. Needs: python 3, torch, transformers; nvidia-smi for power on NVIDIA GPUs.
usage: python measure.py MODEL_ID_OR_PATH [--batches 1 4 16] [--prompt 256] [--new 128] [--out results.json] [--info-only] [--idle-seconds 30]
Steps: (1) memory bandwidth with a copy test, (2) idle power, (3) for each batch size decode `new` tokens from a `prompt`-token input while sampling board power every 0.1 s, (4) write JSON.
Uses the GPU when torch sees one, otherwise the CPU (speed only, power N/A; CPU mode exists for testing the tool).
Close other programs first. Plug a laptop into mains and use the same power mode for every run. Do not touch the machine during a run."""
import argparse, json, subprocess, threading, time
import torch
from transformers import AutoModelForCausalLM

GPU = torch.cuda.is_available(); DEV = "cuda" if GPU else "cpu"
def sync():
    if GPU: torch.cuda.synchronize()

def smi(q):
    try:
        v = subprocess.check_output(["nvidia-smi", "--query-gpu=" + q, "--format=csv,noheader,nounits"], text=True, stderr=subprocess.DEVNULL).strip().split("\n")[0]
        return float(v)
    except Exception:
        return None

class Sampler(threading.Thread):
    def __init__(s): super().__init__(daemon=True); s.v = []; s.run_flag = True
    def run(s):
        while s.run_flag:
            p = smi("power.draw") if GPU else None
            if p is not None: s.v.append(p)
            time.sleep(0.1)

def bandwidth_gbs():
    n = (256 if GPU else 64) * 1024 * 1024 // 2  # fp16 elements
    a = torch.empty(n, dtype=torch.float16, device=DEV); b = torch.empty_like(a); sync()
    for _ in range(3): b.copy_(a)
    sync(); t = time.time(); k = 20 if GPU else 5
    for _ in range(k): b.copy_(a)
    sync(); dt = time.time() - t
    return 2 * a.numel() * 2 * k / dt / 1e9  # read + write bytes

ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--batches", type=int, nargs="+", default=[1, 4, 16])
ap.add_argument("--prompt", type=int, default=256); ap.add_argument("--new", type=int, default=128); ap.add_argument("--out", default="results.json")
ap.add_argument("--info-only", action="store_true", help="measure only the device name, copy bandwidth and idle power, then stop"); ap.add_argument("--idle-seconds", type=int, default=30)
a = ap.parse_args()
if GPU: dev = torch.cuda.get_device_properties(0); name, vram = dev.name, dev.total_memory / 1e9
else: name, vram = "CPU (test mode)", 16.0
res = {"gpu": name, "vram_gb": vram, "device": DEV, "torch": torch.__version__, "model": a.model, "prompt": a.prompt, "new": a.new, "runs": []}
res["bandwidth_copy_gbs"] = bandwidth_gbs()
print("device", name, "copy bandwidth GB/s", round(res["bandwidth_copy_gbs"], 1))
smp = Sampler(); smp.start(); time.sleep(a.idle_seconds); idle = smp.v[:]; smp.v = []
res["idle_power_w"] = sum(idle) / len(idle) if idle else None; print("idle power W", res["idle_power_w"])
if a.info_only:
    smp.run_flag = False; json.dump(res, open(a.out, "w"), indent=1); print("info written", a.out, "(send this file; no model was run)"); raise SystemExit
dt_ = torch.float16 if GPU else torch.float32
model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=dt_).to(DEV).eval()
res["weight_bytes"] = sum(p.numel() * p.element_size() for p in model.parameters())
cfg = model.config; heads = getattr(cfg, "num_attention_heads", getattr(cfg, "n_head", None)); hidden = getattr(cfg, "hidden_size", getattr(cfg, "n_embd", None))
res["layers"] = getattr(cfg, "num_hidden_layers", getattr(cfg, "n_layer", None)); res["hidden"] = hidden; res["heads"] = heads
res["kv_heads"] = getattr(cfg, "num_key_value_heads", heads); res["dtype_bytes"] = 2 if GPU else 4
vocab = cfg.vocab_size
for B in a.batches:
    try:
        ids = torch.randint(0, vocab, (B, a.prompt), device=DEV); att = torch.ones_like(ids)
        if GPU: torch.cuda.reset_peak_memory_stats()
        with torch.no_grad():
            model.generate(ids, attention_mask=att, max_new_tokens=4, min_new_tokens=4, do_sample=False, pad_token_id=0)  # warm-up
            sync(); smp.v = []; time.sleep(1.0); smp.v = []
            t0 = time.time(); out = model.generate(ids, attention_mask=att, max_new_tokens=a.new, min_new_tokens=a.new, do_sample=False, pad_token_id=0); sync(); t1 = time.time()
        pw = list(smp.v); gen = out.shape[1] - a.prompt
        r = {"batch": B, "seconds": t1 - t0, "new_tokens": gen, "tokens_per_s_total": B * gen / (t1 - t0), "tokens_per_s_per_user": gen / (t1 - t0),
             "mean_power_w": sum(pw) / len(pw) if pw else None, "peak_mem_gb": torch.cuda.max_memory_allocated() / 1e9 if GPU else None}
        if r["mean_power_w"] is not None:
            r["joules_per_token_gross"] = r["mean_power_w"] * (t1 - t0) / (B * gen)
            if res["idle_power_w"] is not None: r["joules_per_token_net"] = (r["mean_power_w"] - res["idle_power_w"]) * (t1 - t0) / (B * gen)
        else: r["note"] = "power N/A"
        print(r); res["runs"].append(r)
    except torch.cuda.OutOfMemoryError:
        print("batch", B, "out of memory"); res["runs"].append({"batch": B, "error": "out of memory"}); torch.cuda.empty_cache()
smp.run_flag = False
json.dump(res, open(a.out, "w"), indent=1); print("written", a.out)
