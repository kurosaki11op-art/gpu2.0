#!/usr/bin/env python3
"""Energy-per-token measurement for one machine (wedge 1, test G1). Run this on the machine being measured. Needs: python 3, torch, transformers; nvidia-smi for power on NVIDIA GPUs.
usage: python measure.py MODEL_ID_OR_PATH [--batches 1 4 16] [--prompt 256] [--new 128] [--out results.json] [--info-only] [--idle-seconds 30]
Steps: (1) memory bandwidth with a copy test, (2) idle power, (3) for each batch size decode `new` tokens from a `prompt`-token input while sampling board power every 0.1 s, (4) write JSON (after every batch, so a later failure keeps the earlier results).
Uses the GPU when torch sees one, otherwise the CPU (speed only, power N/A; CPU mode exists for testing the tool).
Before each batch the tool prints the batch size, free and total GPU memory and an estimate of the cache it needs. Out-of-memory failures (PyTorch's allocator error and the CUDA runtime's own "out of memory" error) are recorded for that batch with the memory state, and the run goes on; any other error stops the run, after saving what was measured.
Close other programs first (browsers, games, anything using the GPU). Plug a laptop into mains and use the same power mode for every run. Do not touch the machine during a run."""
import argparse, gc, json, subprocess, threading, time
import torch
from transformers import AutoModelForCausalLM

GPU = torch.cuda.is_available(); DEV = "cuda" if GPU else "cpu"
OOM_TYPES = (torch.cuda.OutOfMemoryError,)

def sync():
    if GPU: torch.cuda.synchronize()

def is_oom(e):
    """True for PyTorch's allocator OOM, or a CUDA runtime error whose message says out of memory (torch.AcceleratorError). Anything else is not an OOM and must propagate."""
    if isinstance(e, OOM_TYPES): return True
    acc = getattr(torch, "AcceleratorError", None)
    return acc is not None and isinstance(e, acc) and "out of memory" in str(e).lower()

def mem_state():
    """Free and total device memory as the driver sees it (includes other programs), plus what this process holds."""
    if not GPU: return {"free_gb": None, "total_gb": None, "torch_allocated_gb": None, "torch_reserved_gb": None}
    free, total = torch.cuda.mem_get_info()
    return {"free_gb": free / 1e9, "total_gb": total / 1e9, "torch_allocated_gb": torch.cuda.memory_allocated() / 1e9, "torch_reserved_gb": torch.cuda.memory_reserved() / 1e9}

def fmt(m): return "free %.2f of %.2f GB (this process: allocated %.2f, reserved %.2f)" % (m["free_gb"], m["total_gb"], m["torch_allocated_gb"], m["torch_reserved_gb"]) if GPU else "cpu"

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
    r = 2 * a.numel() * 2 * k / dt / 1e9  # read + write bytes
    del a, b; gc.collect()
    if GPU: torch.cuda.empty_cache()
    return r

def kv_estimate_gb(res, B, ctx):
    """Cache bytes for B sequences of ctx tokens (K and V, every layer). Estimate only."""
    try:
        hd = res["hidden"] // res["heads"]; return B * ctx * 2 * res["layers"] * res["kv_heads"] * hd * res["dtype_bytes"] / 1e9
    except Exception:
        return None

def run_batch(model, smp, res, B, a, vocab):
    """One batch size: warm-up, then the timed decode. Temporary tensors are released by the caller's cleanup."""
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
    return r

def release():
    gc.collect()
    if GPU: torch.cuda.empty_cache()

def save(res, path): json.dump(res, open(path, "w"), indent=1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--batches", type=int, nargs="+", default=[1, 4, 16])
    ap.add_argument("--prompt", type=int, default=256); ap.add_argument("--new", type=int, default=128); ap.add_argument("--out", default="results.json")
    ap.add_argument("--info-only", action="store_true", help="measure only the device name, copy bandwidth and idle power, then stop"); ap.add_argument("--idle-seconds", type=int, default=30)
    a = ap.parse_args()
    if GPU: dev = torch.cuda.get_device_properties(0); name, vram = dev.name, dev.total_memory / 1e9
    else: name, vram = "CPU (test mode)", 16.0
    res = {"gpu": name, "vram_gb": vram, "device": DEV, "torch": torch.__version__, "model": a.model, "prompt": a.prompt, "new": a.new, "runs": []}
    print("device", name, "|", fmt(mem_state()))
    res["bandwidth_copy_gbs"] = bandwidth_gbs(); print("copy bandwidth GB/s", round(res["bandwidth_copy_gbs"], 1))
    smp = Sampler(); smp.start(); time.sleep(a.idle_seconds); idle = smp.v[:]; smp.v = []
    res["idle_power_w"] = sum(idle) / len(idle) if idle else None; print("idle power W", res["idle_power_w"])
    res["memory_before_model"] = mem_state()
    if a.info_only:
        smp.run_flag = False; save(res, a.out); print("info written", a.out, "(send this file; no model was run)"); return
    dt_ = torch.float16 if GPU else torch.float32
    try: model = AutoModelForCausalLM.from_pretrained(a.model, dtype=dt_)  # newer transformers
    except TypeError: model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=dt_)  # older ones
    model = model.to(DEV).eval()
    res["weight_bytes"] = sum(p.numel() * p.element_size() for p in model.parameters())
    cfg = model.config; heads = getattr(cfg, "num_attention_heads", getattr(cfg, "n_head", None)); hidden = getattr(cfg, "hidden_size", getattr(cfg, "n_embd", None))
    res["layers"] = getattr(cfg, "num_hidden_layers", getattr(cfg, "n_layer", None)); res["hidden"] = hidden; res["heads"] = heads
    res["kv_heads"] = getattr(cfg, "num_key_value_heads", heads); res["dtype_bytes"] = 2 if GPU else 4
    res["memory_after_load"] = mem_state(); print("model loaded: weights %.2f GB |" % (res["weight_bytes"] / 1e9), fmt(res["memory_after_load"]))
    vocab = cfg.vocab_size
    try:
        for B in a.batches:
            m0 = mem_state(); kv = kv_estimate_gb(res, B, a.prompt + a.new)
            print("batch %d: %s; estimated cache %s GB" % (B, fmt(m0), "%.3f" % kv if kv is not None else "n/a"), flush=True)
            try:
                r = run_batch(model, smp, res, B, a, vocab); r["memory_before"] = m0; print(r); res["runs"].append(r)
            except Exception as e:
                if not is_oom(e): raise  # not an out-of-memory error: do not hide it (results so far are saved below)
                m1 = mem_state(); print("batch %d: OUT OF MEMORY (%s: %s) | %s" % (B, type(e).__name__, str(e).splitlines()[0][:200], fmt(m1)))
                res["runs"].append({"batch": B, "error": "out of memory", "exception": type(e).__name__, "message": str(e)[:300], "memory_before": m0, "memory_at_failure": m1})
                release()
                try:
                    torch.zeros(1, device=DEV); sync()  # is the CUDA context still usable?
                except Exception as e2:
                    print("CUDA context is not usable after the error (%s); stopping this run, results so far are saved." % type(e2).__name__); res["stopped_after"] = B; break
            finally:
                release()
            save(res, a.out)  # after every batch
    finally:
        smp.run_flag = False; save(res, a.out)
    print("written", a.out)

if __name__ == "__main__":
    main()
