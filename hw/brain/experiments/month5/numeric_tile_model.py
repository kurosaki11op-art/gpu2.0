"""28 Oct 2026, ESTIMATED (an order-of-magnitude energy model, plus or minus 3x; no hardware, no simulation of a real chip). NUMERIC TILE STUDY: a benchmark list for the things GPUs do beyond L (dense linear algebra, FFT, sparse/stencil physics solvers, filters, rendering, big-model inference) and where their energy goes under two architectures.
 GPU-style baseline: dense units, operands from a 1 MB-class on-chip cache, working set in external HBM; naive precision as the workload states it (fp64 for physics), and a mixed-precision variant (what modern GPUs can also do) so the comparison is fair.
 Our numeric tile (a design hypothesis, not a build): (a) memory next to the compute in many small banks (48 KB-class SRAM, Cerebras-style), (b) the whole working set on chip when it fits ONCHIP_MB, spilled to HBM otherwise, (c) zero skipping where the data is sparse (event driven), (d) precision routing: bulk work in low precision, a small routed fraction in high precision (iterative refinement).
Constants (pJ). Set '45nm': Horowitz ISSCC 2014 (fp32 mult 3.7, add 0.9; fp16 mult 1.1, add 0.4; int8 mult 0.2, add 0.03; SRAM 64-bit read 10 pJ at 8 KB, 20 at 32 KB, 100 at 1 MB; DRAM 1300 per 64 bits); fp64 is NOT in that table: assumed 4x fp32 mult (14.8) and 2.5x add (2.25), an assumption. Set 'modern': compute = 45 nm values x 0.2 (assumed scaling to about 7 nm); HBM3E 5.74 pJ/bit with IO (LLMET, arXiv 2607.26491, MODELLED, our memory_technology_study note); large on-chip SRAM 0.495 pJ/bit at 40 MB rising to 2.78 pJ/bit at 1 GB (same paper, ESTIMATED); small banks (48 KB) 20 pJ per 64 bits x 0.2.
Workload sizes are round numbers chosen to be typical, not measurements. env: ONCHIP_MB."""
import os, math
ONCHIP_MB = float(os.environ.get("ONCHIP_MB", 256)); ONCHIP = ONCHIP_MB * 1e6
E45 = dict(mul=dict(fp64=14.8, fp32=3.7, fp16=1.1, int8=0.2), add=dict(fp64=2.25, fp32=0.9, fp16=0.4, int8=0.03), cache=100.0, bank=20.0, hbm=1300.0, big_sram=lambda mb: 100.0)
def modern_big_sram(mb):                                                                                    # pJ per 64-bit word, interpolating 0.495 pJ/bit at 40 MB to 2.78 pJ/bit at 1024 MB (log scale)
    mb = max(mb, 40.0); f = (math.log(mb) - math.log(40.0)) / (math.log(1024.0) - math.log(40.0)); return 64 * (0.495 + f * (2.78 - 0.495))
EMOD = dict(mul={k: 0.2 * v for k, v in E45["mul"].items()}, add={k: 0.2 * v for k, v in E45["add"].items()}, cache=0.2 * 100.0, bank=0.2 * 20.0, hbm=64 * 5.74, big_sram=modern_big_sram)
# name: mults, adds, precision, working set bytes, GPU traffic bytes to external memory, on-chip words per op (reuse), skippable fraction (zeros), precision-routing: fraction that must stay high precision (1.0 = no routing possible), notes
W = [
 ("Dense matrix multiply 4096^3 fp32", 6.87e10, 6.87e10, "fp32", 201e6, 4.3e9, 0.0625, 0.0, 1.0, "high reuse, compute bound"),
 ("3D FFT 512^3 complex fp32", 9.1e9, 9.1e9, "fp32", 1.07e9, 6.4e9, 1.0, 0.0, 1.0, "low reuse, memory bound"),
 ("3D Poisson solve 256^3, CG 200 its, fp64", 3.4e10, 3.4e10, "fp64", 0.54e9, 2.1e11, 1.0, 0.0, 0.10, "stencil SpMV, memory bound, mixed precision possible"),
 ("CFD stencil 512^3 x 100 steps, fp64", 7e11, 7e11, "fp64", 2.1e9, 4.3e11, 0.5, 0.0, 0.10, "13 flops per point per step"),
 ("Kalman filter 12 states x 1e6 steps, fp64", 1e10, 1e10, "fp64", 1e5, 1e5, 0.25, 0.0, 1.0, "tiny dense, latency bound, fits anywhere"),
 ("Neural network inference int8 x 1e6 images (small)", 2.5e11, 2.5e11, "int8", 6e4, 6e10, 0.25, 0.5, 1.0, "ReLU activations about half zeros"),
 ("LLM token generation, 1B params int8 x 100 tokens", 1e11, 1e11, "int8", 1e9, 1e11, 0.0625, 0.0, 1.0, "weights streamed each token, no reuse"),
 ("Ray tracing 1080p frame, 2M rays, 500 MB scene, fp32", 2.4e9, 2.4e9, "fp32", 500e6, 1.5e9, 0.5, 0.0, 1.0, "irregular pointer chasing"),
 ("Sparse recognition (L-like) x 1e6 images: 4608 inputs x 10 classes", 4.6e10, 4.6e10, "int8", 8.4e4, 0.0, 0.0625, 0.87, 1.0, "dense baseline does every input; the event-driven tile skips the 87% that are off"),
]
def energy(w, E, arch, mixed=False):
    name, mu, ad, prec, U, traffic, reuse, sparse, hi, _ = w
    skip = (1 - sparse) if arch == "tile" else 1.0
    if mixed or arch == "tile":                                                                                 # bulk in fp32 (or int8 stays int8), a routed fraction in the stated precision
        lo = {"fp64": "fp32"}.get(prec, prec); share_hi = hi if prec == "fp64" else 1.0
        e_mul = share_hi * E["mul"][prec] + (1 - share_hi) * E["mul"][lo]; e_add = share_hi * E["add"][prec] + (1 - share_hi) * E["add"][lo]
    else: e_mul, e_add = E["mul"][prec], E["add"][prec]
    compute = skip * (mu * e_mul + ad * e_add)
    words = skip * (mu + ad) * reuse
    if arch == "gpu": onchip = words * E["cache"]; main = traffic / 8 * E["hbm"]
    else:
        onchip = words * E["bank"]
        if U <= ONCHIP: main = U / 8 * E["hbm"]                                                                  # loaded once
        else: main = (traffic * (1 - ONCHIP / U) + ONCHIP) / 8 * E["hbm"] * (skip if sparse else 1.0)
        if U > 1e6: onchip += skip * (mu + ad) * reuse * 0.0
    return compute, onchip, main
for setname, E in (("45nm", E45), ("modern", EMOD)):
    print("\n=== constant set: %s | on-chip capacity %.0f MB ===" % (setname, ONCHIP_MB))
    print("%-58s %12s %12s %12s %9s %9s  %s" % ("workload", "GPU naive J", "GPU mixed J", "tile J", "gain vs naive", "vs mixed", "where the tile's energy goes (compute/on-chip/external)"))
    for w in W:
        g = energy(w, E, "gpu"); gm = energy(w, E, "gpu", mixed=True); t = energy(w, E, "tile"); sg, sgm, st = sum(g) * 1e-12, sum(gm) * 1e-12, sum(t) * 1e-12
        print("%-58s %12.3g %12.3g %12.3g %8.1fx %8.1fx  %2.0f%%/%2.0f%%/%2.0f%%" % (w[0][:58], sg, sgm, st, sg / st if st else float("inf"), sgm / st if st else float("inf"), 100 * t[0] / sum(t), 100 * t[1] / sum(t), 100 * t[2] / sum(t)))
