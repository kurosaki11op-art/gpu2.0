"""28 Oct 2026, ESTIMATED. MEMORY TECHNOLOGY OPTIONS on the SRAM area/cost model (base scenario of sram_area_cost_model.py). Density multipliers over 6T SRAM are REFERENCE claims from papers (gain cell 1.5x [HyGain, after periphery] to 2x [3T industrial designs]; STT-MRAM 2-3x cell reduction; vertical stacking of n memory layers multiplies density by n at an extra wafer cost per layer, a proposal-level figure up to 22x in a DATE 2026 design) and have not been verified by us. Refresh/write energy and speed penalties are NOT modelled; extra layer cost is an ASSUMPTION (each added layer costs 0.6 of a base die)."""
import math
s = dict(dens=24.0, wafer=17000, d0=0.10, hbm=15); LOGIC = 150.0; MAXDIE = 600.0; WA = math.pi * 150 ** 2
def yld(a): x = a / 100 * s["d0"]; return ((1 - math.exp(-x)) / x) ** 2
def dc(a): return s["wafer"] / (WA * 0.85 / a * yld(a))
opts = [("6T SRAM (baseline)", 1.0, 1, 0), ("gain cell, 1.5x", 1.5, 1, 0), ("gain cell, 2x", 2.0, 1, 0), ("STT-MRAM, 2.5x", 2.5, 1, 0), ("SRAM stacked 2 layers", 1.0, 2, 1), ("SRAM stacked 4 layers", 1.0, 4, 1), ("gain cell 2x stacked 4 layers", 2.0, 4, 1)]
print("%-30s %10s %10s %12s %12s %12s" % ("option", "1 GB mm2 footprint", "1 GB $", "4 GB footprint", "4 GB $", "44 GB $"))
for nm, mult, layers, _ in opts:
    out = []
    for mb in (1024, 4096, 44000):
        sram = mb * 8e6 / (s["dens"] * mult * 1e6) / layers; tot = sram + LOGIC; nd = math.ceil(tot / MAXDIE); a = tot / nd; c = nd * dc(a) * (1 + 0.6 * (layers - 1)); out.append((tot, c))
    print("%-30s %10.0f %10.0f %12.0f %12.0f %12.0f" % (nm, out[0][0], out[0][1], out[1][0], out[1][1], out[2][1]))
