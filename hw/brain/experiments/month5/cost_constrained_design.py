"""28 Oct 2026, ESTIMATED. COST-CONSTRAINED DESIGN: what 1 GB and 2 GB of on-chip memory costs in rupees, and which levers lower it. Same ASSUMED/REFERENCE inputs as cost_by_node.py (wafer price, SRAM density, defect density, NRE low/high), plus: (1) per-tile logic when memory is split into 48 KB banks each with its own compute (Cerebras-like): 0.025 mm2 at 5 nm (half of their 0.05 mm2 core, from the Cerebras study) versus an ASSUMED add-only ternary tile of 0.005 mm2; logic area relative to 5 nm: x5 at 16 nm and x12 at 28 nm (ASSUMED rough density ratios); (2) bits stored per parameter: int8 8, ternary 2-bit 2, packed 1.58; (3) exchange rate 85 INR per USD (ASSUMED). Price = 2.5 x silicon + NRE/volume."""
import math
FX = 85.0; WA = math.pi * 150 ** 2; MAXDIE = 600.0
N = {"28nm": dict(w=3000, dens=7, d0=0.05, nm=28, nre=(1.5e6, 45e6)), "16nm": dict(w=4500, dens=14, d0=0.07, nm=16, nre=(2.8e6, 100e6)), "5nm": dict(w=16500, dens=24, d0=0.10, nm=5, nre=(10e6, 480e6))}
def yld(a, d0): x = a / 100 * d0; return ((1 - math.exp(-x)) / x) ** 2
def chip(nd, mb, tile_logic_5nm):
    n = N[nd]; sram = mb * 8e6 / (n["dens"] * 1e6); tiles = mb * 1024 / 48; logic = tiles * tile_logic_5nm * {28: 12, 16: 5, 5: 1}[n["nm"]] if tile_logic_5nm else 150.0
    tot = sram + logic; k = math.ceil(tot / MAXDIE); a = tot / k; return tot, k, k * n["w"] / (WA * 0.85 / a * yld(a, n["d0"]))
cr = lambda usd: usd * FX / 1e7
print("PER-CHIP SILICON (die cost only), 1 GB and 2 GB, by tile logic assumption; rupees in thousands (Rs k)")
print("%-6s %-5s %-34s %9s %5s %11s" % ("node", "GB", "logic assumption", "mm2", "dies", "silicon Rs k"))
for nd in N:
    for gb in (1, 2):
        for lab, tl in (("shared 150 mm2 logic (earlier)", 0), ("Cerebras-size tile 0.025 mm2", 0.025), ("add-only tile 0.005 mm2 (assumed)", 0.005)):
            t, k, c = chip(nd, gb * 1024, tl); print("%-6s %-5d %-34s %9.0f %5d %11.1f" % (nd, gb, lab, t, k, c * FX / 1e3))
print("\nONE-TIME COST (NRE: masks + design + IP), crore rupees (1 crore = 1e7): low case / high case")
for nd in N: print("  %-5s Rs %.1f crore (low) / Rs %.0f crore (high)" % (nd, cr(N[nd]["nre"][0]), cr(N[nd]["nre"][1])))
print("\nSTORAGE LEVER: MB needed per model size and bits per parameter")
for p in (1e6, 1e8, 1e9, 4e9): print("  %5.0fM params: int8 %8.0f MB | ternary 2-bit %8.0f MB | packed 1.58-bit %8.0f MB" % (p / 1e6, p / 1e6, p * 2 / 8 / 1e6, p * 1.58 / 8 / 1e6))
print("\nPER-CHIP PRICE at volume incl. NRE share (add-only tile, 1 GB, 2.5x package/margin), Rs k: NRE low / high")
for nd in N:
    t, k, c = chip(nd, 1024, 0.005)
    for v in (1e3, 1e4, 1e5): print("  %-5s volume %7d: Rs %9.0f k (low NRE) / Rs %10.0f k (high NRE)" % (nd, v, (2.5 * c + N[nd]["nre"][0] / v) * FX / 1e3, (2.5 * c + N[nd]["nre"][1] / v) * FX / 1e3))
