"""28 Oct 2026, ESTIMATED (order of magnitude; the biggest unknown of the L Forge design was the tile-to-tile traffic, absent from numeric_tile_model.py). Adds the fabric energy of moving data between tiles to the tile energy of numeric_tile_model.py at 2,048 MB (modern constants) and recomputes the gain over the GPU mixed-precision baseline. ASSUMPTIONS: 1,024 tiles of 2 MB as a 32 x 32 mesh on 3 dies (a tile here is a group of 40 of the 48 KB banks; hop = one mesh link); link plus router energy per bit per hop swept 0.02, 0.05, 0.2 pJ (REASONING from on-chip wire energy of about 0.1 pJ/bit/mm and 0.2 mm tile pitch, not a measurement); die-to-die link 0.7 pJ/bit with the fraction of traffic that crosses dies given per pattern (0.03 for neighbour exchange, 2/3 for all-to-all or random). Traffic volumes are computed from standard decompositions (SUMMA matrix multiply, pencil-decomposed 3D FFT, 3D domain decomposition for stencils with halo exchange and the 2D-mesh folding factor 3, activation broadcast for the language model, random node fetches for ray tracing)."""
import io, os, contextlib
os.environ["ONCHIP_MB"] = "2048"
with contextlib.redirect_stdout(io.StringIO()): import numeric_tile_model as m
p = 32; T = p * p; mean_hops = 2 * p / 3
K = {}   # name: (bits moved, average hops, die-crossing fraction)
N = 4096; K["Dense matrix multiply"] = (2 * N * N * p * 8 * 1.0625, 1.0, 2 / 3)
K["3D FFT"] = (2 * (512 ** 3) * 4 * 8, mean_hops, 2 / 3)
K["Poisson CG"] = (T * 6 * (256 / 10) ** 2 * 8 * 8 * 200, 3.0, 0.03)
K["CFD stencil"] = (T * 6 * (512 / 10) ** 2 * 5 * 8 * 8 * 100, 3.0, 0.03)
K["LLM 1B int8"] = (2048 * T * 8 * 5 * 24 * 100, 1.0, 2 / 3)
K["Ray tracing"] = (2e6 * 50 * 64 * 8, mean_hops, 2 / 3)
names = {w[0]: w for w in m.W}; key = {"Dense matrix multiply": "Dense matrix multiply 4096^3 fp32", "3D FFT": "3D FFT 512^3 complex fp32", "Poisson CG": "3D Poisson solve 256^3, CG 200 its, fp64", "CFD stencil": "CFD stencil 512^3 x 100 steps, fp64", "LLM 1B int8": "LLM token generation, 1B params int8 x 100 tokens", "Ray tracing": "Ray tracing 1080p frame, 2M rays, 500 MB scene, fp32"}
print("FABRIC ENERGY and the revised gain over a mixed-precision GPU baseline (2 GB on chip, modern constants, ESTIMATED)")
print("%-24s %9s %9s | %-34s | %-34s | %-34s" % ("kernel", "GPU J", "tile J", "hop 0.02 pJ/bit: fabric J, gain", "hop 0.05 pJ/bit: fabric J, gain", "hop 0.2 pJ/bit: fabric J, gain"))
for k, (bits, hops, fc) in K.items():
    w = names[key[k]]; g = sum(m.energy(w, m.EMOD, "gpu", True)) * 1e-12; t = sum(m.energy(w, m.EMOD, "tile")) * 1e-12; row = []
    for e in (0.02, 0.05, 0.2): f = bits * hops * e * 1e-12 + bits * fc * 0.7e-12; row.append("%9.3g J, %5.1fx -> %5.1fx" % (f, g / t, g / (t + f)))
    print("%-24s %9.3g %9.3g | %s" % (k, g, t, " | ".join(row)))
print("\nNo fabric traffic: Kalman (one tile), small network and sparse recognition (tables stay local); their gains are unchanged.")
