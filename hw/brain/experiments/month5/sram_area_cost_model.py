"""28 Oct 2026, ESTIMATED (order of magnitude, no foundry quote, no layout). SRAM AREA AND COST MODEL for the numeric tile: what does 64 / 256 / 1024 MB of on-chip memory cost in silicon, yield, leakage, against buying the same bytes as HBM? Reference values: N5/N3E high-density SRAM bitcell 0.021 um2 and macro density about 31.8 Mb/mm2 (public reporting, Tom's Hardware/WikiChip, 2022-23; REFERENCE, not verified by us); reticle limit 858 mm2; Cerebras WSE-3 44 GB SRAM on 46,225 mm2 (VENDOR CLAIM). ASSUMPTIONS (unsourced, swept low/base/high): usable macro density incl. periphery and redundancy, wafer cost, defect density, HBM $/GB, leakage per bit, logic area. Yield = Murphy model."""
import math
SC = {"low (optimistic)": dict(dens=31.8, wafer=12000, d0=0.07, hbm=10, leak=20e-12), "base": dict(dens=24.0, wafer=17000, d0=0.10, hbm=15, leak=60e-12), "high (pessimistic)": dict(dens=16.0, wafer=25000, d0=0.15, hbm=25, leak=200e-12)}
LOGIC = 150.0; MAXDIE = 600.0; WAFER_AREA = math.pi * 150 ** 2
def yld(a, d0): x = a / 100 * d0; return ((1 - math.exp(-x)) / x) ** 2 if x > 0 else 1.0
def die_cost(a, s): n = WAFER_AREA * 0.85 / a; return s["wafer"] / (n * yld(a, s["d0"]))
for nm, s in SC.items():
    print("\n== scenario %s: macro density %.1f Mb/mm2, wafer $%d, D0 %.2f/cm2, HBM $%d/GB, leakage %.0f pW/bit ==" % ((nm, s["dens"], s["wafer"], s["d0"], s["hbm"], s["leak"] * 1e12)))
    print("%-9s %12s %6s %12s %14s %12s %10s %14s" % ("capacity", "SRAM mm2", "dies", "silicon $", "same bytes HBM $", "SRAM/HBM $", "leak W", "1B-LLM fits?"))
    for mb in (64, 256, 1024, 4096, 44000):
        sram = mb * 8e6 / (s["dens"] * 1e6); tot = sram + LOGIC; nd = math.ceil(tot / MAXDIE); a = tot / nd; cost = nd * die_cost(a, s); hbm = mb / 1000 * s["hbm"]
        print("%-9s %12.0f %6d %12.0f %14.1f %11.0fx %10.2f %14s" % ("%d MB" % mb, sram, nd, cost, hbm, cost / hbm, mb * 8e6 * s["leak"], "yes" if mb >= 1024 else "no"))
print("\nCerebras WSE-3 claim check: 44 GB / 46,225 mm2 = %.1f Mb/mm2 whole wafer (includes cores and wiring) against %.1f Mb/mm2 macro density" % (44e9 * 8 / 46225 / 1e6, 31.8))
