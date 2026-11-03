#!/usr/bin/env python3
"""L Compute step 4 GPU runner (bars P2, P3, P4 of lcompute/docs/ROADMAP.md).

Runs the PTX that `lcompute --emit-gpu DIR` wrote, on a real NVIDIA GPU through the CUDA driver API (ctypes, no compiler needed),
and compares every output buffer bit for bit with what the reference interpreter produced.

  usage:  python3 gpu_runner.py DIR            # DIR from `lcompute --emit-gpu DIR`
          python3 gpu_runner.py DIR --parse    # no GPU needed: only checks that the files parse

ABI (see src/ptx.rs): a buffer argument is (u64 device pointer, s32 length in floats); a scalar is one parameter; the last parameter is a u64 pointer to a u32 error word.
"""
import ctypes, os, sys, time
import numpy as np

def parse_meta(path):
    m = {"args": []}
    for line in open(path):
        t = line.split()
        if not t: continue
        if t[0] == "kernel": m["kernel"] = t[1]
        elif t[0] == "grid": m["grid"] = tuple(int(x) for x in t[1:4])
        elif t[0] == "block": m["block"] = tuple(int(x) for x in t[1:4])
        elif t[0] == "expect": m["expect"] = t[1]
        elif t[0] == "arg": m["args"].append(tuple(t[1:]))
    return m

def load_cases(d):
    cases = []
    for name in sorted(os.listdir(os.path.join(d, "cases"))):
        cd = os.path.join(d, "cases", name); m = parse_meta(os.path.join(cd, "meta.txt")); m["name"] = name; m["dir"] = cd; cases.append(m)
    return cases

class Cuda:
    def __init__(self):
        self.lib = ctypes.CDLL("libcuda.so.1")
        self.check(self.lib.cuInit(0), "cuInit")
        dev = ctypes.c_int(); self.check(self.lib.cuDeviceGet(ctypes.byref(dev), 0), "cuDeviceGet")
        name = ctypes.create_string_buffer(100); self.lib.cuDeviceGetName(name, 100, dev); self.name = name.value.decode()
        maj, mi = ctypes.c_int(), ctypes.c_int(); self.lib.cuDeviceGetAttribute(ctypes.byref(maj), 75, dev); self.lib.cuDeviceGetAttribute(ctypes.byref(mi), 76, dev); self.cc = (maj.value, mi.value)
        ctx = ctypes.c_void_p(); self.check(self.lib.cuDevicePrimaryCtxRetain(ctypes.byref(ctx), dev), "cuDevicePrimaryCtxRetain"); self.check(self.lib.cuCtxSetCurrent(ctx), "cuCtxSetCurrent")
        self.mods = {}
    def check(self, r, what):
        if r != 0:
            s = ctypes.c_char_p(); self.lib.cuGetErrorString(r, ctypes.byref(s)); raise RuntimeError(f"{what}: CUDA error {r} {s.value.decode() if s.value else ''}")
    def function(self, ptx_path, kernel):
        if kernel not in self.mods:
            src = open(ptx_path, "rb").read() + b"\0"; mod = ctypes.c_void_p(); self.check(self.lib.cuModuleLoadData(ctypes.byref(mod), src), f"load {kernel}")
            fn = ctypes.c_void_p(); self.check(self.lib.cuModuleGetFunction(ctypes.byref(fn), mod, kernel.encode()), f"get {kernel}"); self.mods[kernel] = fn
        return self.mods[kernel]
    def alloc(self, nbytes):
        p = ctypes.c_uint64(); self.check(self.lib.cuMemAlloc_v2(ctypes.byref(p), ctypes.c_size_t(max(nbytes, 4))), "cuMemAlloc"); return p.value
    def to_dev(self, arr):
        p = self.alloc(arr.nbytes); self.check(self.lib.cuMemcpyHtoD_v2(ctypes.c_uint64(p), arr.ctypes.data_as(ctypes.c_void_p), ctypes.c_size_t(arr.nbytes)), "HtoD"); return p
    def from_dev(self, p, n):
        out = np.empty(n, dtype=np.float32); self.check(self.lib.cuMemcpyDtoH_v2(out.ctypes.data_as(ctypes.c_void_p), ctypes.c_uint64(p), ctypes.c_size_t(out.nbytes)), "DtoH"); return out
    def free(self, p): self.lib.cuMemFree_v2(ctypes.c_uint64(p))
    def launch(self, fn, grid, block, params):
        arr = (ctypes.c_void_p * len(params))(*[ctypes.cast(ctypes.pointer(p), ctypes.c_void_p) for p in params])
        self.check(self.lib.cuLaunchKernel(fn, *grid, *block, 0, None, arr, None), "cuLaunchKernel"); self.check(self.lib.cuCtxSynchronize(), "cuCtxSynchronize")

def run_case(cu, d, c):
    fn = cu.function(os.path.join(d, "ptx", c["kernel"] + ".ptx"), c["kernel"]); params, bufs, keep = [], [], []
    for a in c["args"]:
        if a[0] == "buf":
            arr = np.fromfile(os.path.join(c["dir"], a[1] + "_in.bin"), dtype=np.float32); p = cu.to_dev(arr); bufs.append((a[1], p, arr.size)); keep += [ctypes.c_uint64(p), ctypes.c_int32(arr.size)]
        elif a[0] == "i32": keep.append(ctypes.c_int32(int(a[1])))
        elif a[0] == "f32": keep.append(ctypes.c_float(float(a[1])))
    err = cu.to_dev(np.zeros(1, dtype=np.float32)); keep.append(ctypes.c_uint64(err))
    cu.launch(fn, c["grid"], c["block"], keep)
    ok = True; notes = []
    for base, p, n in bufs:
        got = cu.from_dev(p, n); exp = np.fromfile(os.path.join(c["dir"], base + "_exp.bin"), dtype=np.float32)
        same = np.array_equal(got.view(np.uint32), exp.view(np.uint32)); ok &= same
        if not same: notes.append(f"{base}: {int((got.view(np.uint32) != exp.view(np.uint32)).sum())} of {n} words differ")
        cu.free(p)
    e = int(cu.from_dev(err, 1).view(np.uint32)[0]); cu.free(err)
    if c["expect"] == "ok": ok &= (e == 0); notes.append(f"error word {e}") if e else None
    else: ok &= (e != 0); notes.append(f"error word {e} (instruction {e - 1}), access skipped")
    return ok, "; ".join(n for n in notes if n)

def perf(cu, d):
    n = 1024; a = np.random.default_rng(1).uniform(-1, 1, (n, n)).astype(np.float32); b = np.random.default_rng(2).uniform(-1, 1, (n, n)).astype(np.float32); flop = 2.0 * n ** 3; reps = 20
    pa, pb = cu.to_dev(a.ravel()), cu.to_dev(b.ravel()); results = {}
    ref = None; refms = None
    try:
        import torch
        torch.backends.cuda.matmul.allow_tf32 = False; ta, tb = torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda(); torch.matmul(ta, tb); torch.cuda.synchronize(); best = 1e9
        for _ in range(3):
            t = time.perf_counter()
            for _ in range(reps): r = torch.matmul(ta, tb)
            torch.cuda.synchronize(); best = min(best, (time.perf_counter() - t) / reps)
        ref = r.cpu().numpy(); refms = best; print(f"P4 cuBLAS (PyTorch, TF32 off): {best*1e3:.2f} ms = {flop/best/1e9:.0f} GFLOP/s")
    except ImportError: print("P4: PyTorch not installed, cuBLAS comparison skipped")
    for name, tile in (("matmul_tiled", 16), ("matmul_reg", 64), ("matmul_fma", 64), ("matmul_fma4", 64), ("matmul_fma8", 128)):
        path = os.path.join(d, "ptx", name + ".ptx")
        if not os.path.exists(path): continue
        fn = cu.function(path, name); pc = cu.to_dev(np.zeros(n * n, np.float32)); perr = cu.to_dev(np.zeros(1, np.float32))
        ps = [ctypes.c_uint64(pa), ctypes.c_int32(n * n), ctypes.c_uint64(pb), ctypes.c_int32(n * n), ctypes.c_uint64(pc), ctypes.c_int32(n * n), ctypes.c_int32(n), ctypes.c_int32(n), ctypes.c_int32(n), ctypes.c_uint64(perr)]
        g = (n // tile, n // tile, 1); b16 = (16, 16, 1); cu.launch(fn, g, b16, ps); best = 1e9
        for _ in range(3):
            t = time.perf_counter()
            for _ in range(reps): cu.launch(fn, g, b16, ps)
            best = min(best, (time.perf_counter() - t) / reps)
        got = cu.from_dev(pc, n * n).reshape(n, n); line = f"P4 {name}: {best*1e3:.2f} ms = {flop/best/1e9:.0f} GFLOP/s"
        if refms: line += f"; ours / cuBLAS = {refms/best:.2f}; max |ours - cuBLAS| / max|cuBLAS| = {np.abs(got - ref).max() / np.abs(ref).max():.1e}"
        print(line); results[name] = got
    if "matmul_tiled" in results and "matmul_reg" in results: print("P4 matmul_reg bit-identical to matmul_tiled at 1024^3:", np.array_equal(results["matmul_tiled"].view(np.uint32), results["matmul_reg"].view(np.uint32)))

def main():
    d = sys.argv[1]; cases = load_cases(d)
    if "--parse" in sys.argv: print(f"parsed {len(cases)} cases"); return
    cu = Cuda(); print(f"GPU: {cu.name}, compute capability {cu.cc[0]}.{cu.cc[1]}"); good = 0
    for c in cases:
        ok, note = run_case(cu, d, c); good += ok; print(f"  {c['name']:<28} {'ok' if ok else 'FAIL'}  {note}")
    print(f"P2/P3: {good} of {len(cases)} cases {'PASS' if good == len(cases) else 'FAIL'} (bit-identical to the interpreter; out-of-range reported through the error word)")
    print("P3 note: barrier divergence is not checkable on a GPU (undefined behaviour); it is a CPU back end check only.")
    perf(cu, d)

if __name__ == "__main__": main()
