#!/usr/bin/env python3
"""Test B with a serving engine: batch-1 decode with CUDA graphs on (the engine's default) and off (enforce_eager), on the same engine, against the weights-only floor.
usage (Colab, Linux, GPU runtime; install first and restart the runtime if asked):  !pip -q install vllm
        python graphs_vllm.py MODEL_ID eager|graphs --out vllm_MODEL_MODE.json
Run each mode in its own process (the engine holds the GPU memory), for example:
        !python graphs_vllm.py Qwen/Qwen2.5-0.5B eager  --out vllm_medium_eager.json
        !python graphs_vllm.py Qwen/Qwen2.5-0.5B graphs --out vllm_medium_graphs.json
The result records ms per token at batch 1 (128 new tokens from a 256-token prompt, best of 3), the weights-only floor (weight bytes, taken from the downloaded safetensors files, over the measured copy bandwidth) and the fraction of the floor. If the engine fails to start the error is recorded; send it.
The main-guard matters: the engine starts helper processes by re-importing this file."""
import argparse, glob, json, os, time

def main():
    import torch
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("mode", choices=["eager", "graphs"]); ap.add_argument("--out", default="vllm_result.json")
    ap.add_argument("--new", type=int, default=128); ap.add_argument("--prompt", type=int, default=256)
    a = ap.parse_args()
    def bw():
        n = 256 * 1024 * 1024 // 2; x = torch.empty(n, dtype=torch.float16, device="cuda"); y = torch.empty_like(x); torch.cuda.synchronize()
        for _ in range(3): y.copy_(x)
        torch.cuda.synchronize(); t = time.time()
        for _ in range(20): y.copy_(x)
        torch.cuda.synchronize(); r = 2 * x.numel() * 2 * 20 / (time.time() - t) / 1e9; del x, y; torch.cuda.empty_cache(); return r
    res = {"gpu": torch.cuda.get_device_name(0), "model": a.model, "mode": a.mode, "copy_bandwidth_gbs": bw()}
    try:
        from huggingface_hub import snapshot_download
        res["weight_bytes"] = sum(os.path.getsize(f) for f in glob.glob(os.path.join(snapshot_download(a.model, allow_patterns=["*.safetensors"]), "*.safetensors")))
        import vllm
        from vllm import LLM, SamplingParams
        res["vllm"] = vllm.__version__
        llm = LLM(a.model, dtype="float16", max_model_len=a.prompt + a.new + 16, enforce_eager=(a.mode == "eager"), gpu_memory_utilization=0.6)
        sp = SamplingParams(max_tokens=a.new, min_tokens=a.new, temperature=0.0)
        prompt = {"prompt_token_ids": [100 + (i % 500) for i in range(a.prompt)]}
        for _ in range(3): llm.generate([prompt], sp, use_tqdm=False)  # warm-up
        times = []
        for _ in range(3):
            t = time.time(); out = llm.generate([prompt], sp, use_tqdm=False); times.append(time.time() - t)
        n = len(out[0].outputs[0].token_ids); t = min(times) / n
        floor = res["weight_bytes"] / (res["copy_bandwidth_gbs"] * 1e9)
        res.update({"new_tokens": n, "ms_per_token": t * 1e3, "tokens_per_s": 1 / t, "floor_ms": floor * 1e3, "fraction_of_floor": floor / t})
    except Exception as e:
        res["error"] = "%s: %s" % (type(e).__name__, str(e)[:500])
    print(res); json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
