#!/usr/bin/env python3
"""L Compute: controlled GPU comparison of our matmul kernels against cuBLAS (follow-up to bar Q7).

The first comparison (gpu_runner.py) ran cuBLAS once, first, and our kernels later, with a synchronise after every launch.
Here every round runs cuBLAS and each of our kernels back to back (same order every round), times 20 launches between two CUDA events
(no synchronise inside the loop), logs the GPU clocks and power after each measurement, and reports medians over the rounds, at several sizes.

  usage: python3 gpu_verify.py DIR       # DIR holds ptx/ (from `lcompute --emit-gpu`) and gpu_runner.py
"""
import ctypes, os, subprocess, sys, statistics
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpu_runner import Cuda

KERNELS = [("matmul_fma8db", 128, 128), ("matmul_fma8db_cheap", 128, 128), ("matmul_fma8db_cheap_u", 128, 128), ("matmul_fma8db_none_u", 128, 128), ("matmul_fma8x4_cheap", 128, 64), ("matmul_fma8x4db_cheap", 128, 64)]
SIZES = [512, 1024, 2048, 4096]; ROUNDS = 5; REPS = 20

def smi():
    try:
        o = subprocess.run(["nvidia-smi", "--query-gpu=clocks.sm,clocks.max.sm,power.draw,power.limit,temperature.gpu", "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout.strip()
        return o
    except Exception as e: return f"nvidia-smi unavailable ({e})"

def main():
    d = sys.argv[1]; cu = Cuda(); lib = cu.lib; print(f"GPU: {cu.name}; nvidia-smi at start (sm clock, max sm clock, power W, limit W, temp C): {smi()}")
    import torch
    torch.backends.cuda.matmul.allow_tf32 = False
    def ev(): e = ctypes.c_void_p(); cu.check(lib.cuEventCreate(ctypes.byref(e), 0), "cuEventCreate"); return e
    e0, e1 = ev(), ev()
    def time_ours(fn, g, params):
        cu.launch(fn, g, (16, 16, 1), params)  # warm up (and sync)
        cu.check(lib.cuEventRecord(e0, None), "rec"); 
        for _ in range(REPS): cu.check(lib.cuLaunchKernel(fn, *g, 16, 16, 1, 0, None, (ctypes.c_void_p * len(params))(*[ctypes.cast(ctypes.pointer(p), ctypes.c_void_p) for p in params]), None), "launch")
        cu.check(lib.cuEventRecord(e1, None), "rec"); cu.check(lib.cuEventSynchronize(e1), "sync")
        ms = ctypes.c_float(); cu.check(lib.cuEventElapsedTime(ctypes.byref(ms), e0, e1), "elapsed"); return ms.value / REPS
    def time_torch(ta, tb):
        torch.matmul(ta, tb); torch.cuda.synchronize(); a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True); a.record()
        for _ in range(REPS): torch.matmul(ta, tb)
        b.record(); torch.cuda.synchronize(); return a.elapsed_time(b) / REPS
    for n in SIZES:
        rng = np.random.default_rng(n); a = rng.uniform(-1, 1, (n, n)).astype(np.float32); b = rng.uniform(-1, 1, (n, n)).astype(np.float32); flop = 2.0 * n ** 3
        ta, tb = torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda(); ref = torch.matmul(ta, tb).cpu().numpy(); pa, pb = cu.to_dev(a.ravel()), cu.to_dev(b.ravel()); pc = cu.to_dev(np.zeros(n * n, np.float32)); perr = cu.to_dev(np.zeros(1, np.float32))
        fns = {}; res = {"cuBLAS": []}; clocks = []
        for name, bm, bn in KERNELS:
            fns[name] = (cu.function(os.path.join(d, "ptx", name + ".ptx"), name), (n // bn, n // bm, 1)); res[name] = []
        ps = [ctypes.c_uint64(pa), ctypes.c_int32(n * n), ctypes.c_uint64(pb), ctypes.c_int32(n * n), ctypes.c_uint64(pc), ctypes.c_int32(n * n), ctypes.c_int32(n), ctypes.c_int32(n), ctypes.c_int32(n), ctypes.c_uint64(perr)]
        # correctness of each kernel at this size, once
        errs = {}
        for name, (fn, g) in fns.items(): cu.launch(fn, g, (16, 16, 1), ps); got = cu.from_dev(pc, n * n).reshape(n, n); errs[name] = np.abs(got - ref).max() / np.abs(ref).max()
        for r in range(ROUNDS):
            res["cuBLAS"].append(time_torch(ta, tb)); clocks.append(smi())
            for name, (fn, g) in fns.items(): res[name].append(time_ours(fn, g, ps)); clocks.append(smi())
        cub = statistics.median(res["cuBLAS"]); print(f"\n== {n}x{n}x{n}: {ROUNDS} interleaved rounds, {REPS} launches per timing, CUDA event timing")
        print(f"  {'cuBLAS (PyTorch, TF32 off)':<28} median {cub:8.3f} ms = {flop/cub/1e6:7.0f} GFLOP/s   (rounds: {' '.join(f'{x:.3f}' for x in res['cuBLAS'])})")
        for name, _, _ in KERNELS:
            m = statistics.median(res[name]); print(f"  {name:<28} median {m:8.3f} ms = {flop/m/1e6:7.0f} GFLOP/s   ours/cuBLAS {cub/m:5.2f}   (min {min(res[name]):.3f} max {max(res[name]):.3f} ms; max rel diff to cuBLAS {errs[name]:.1e})")
        sm = [float(c.split(",")[0]) for c in clocks if c and c[0].isdigit()]; pw = [float(c.split(",")[2]) for c in clocks if c and c[0].isdigit()]
        if sm: print(f"  GPU sm clock during this size: {min(sm):.0f} to {max(sm):.0f} MHz, power {min(pw):.0f} to {max(pw):.0f} W")
        for p in (pa, pb, pc, perr): cu.free(p)
        del ta, tb; torch.cuda.empty_cache()

if __name__ == "__main__": main()
