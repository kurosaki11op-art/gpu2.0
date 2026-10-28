"""28 Oct 2026, ESTIMATED. COST BY PROCESS NODE and NRE amortisation. Wafer prices (28nm 3000, 16nm 4500, 7nm 10000, 5nm 16000-17000 USD) are REFERENCE figures from public reporting (siliconanalysts.com, Tom's Hardware, WCCFtech via web search 28 Oct 2026; sources disagree and are not verified by us). SRAM macro densities per node (Mb/mm2: 28nm 7, 16nm 14, 7nm 22, 5nm 24) and defect densities are our ASSUMPTIONS from memory of published bitcell sizes. NRE (mask set + design + IP, USD): 28nm ~5M masks+design low case, 16nm 2.8M, 7nm 5.5M, 5nm 10M are the aggregator's mask+NRE lines; IBS full-design estimates are far higher (28nm ~40-50M, 5nm ~450-540M) -- both shown; the truth for a small team using licensed IP is unknown. Package/test/margin multiplier on silicon: 2.5x ASSUMED."""
import math
WA = math.pi * 150 ** 2
N = {"28nm": dict(w=3000, dens=7, d0=0.05, nre_lo=1.5e6, nre_hi=45e6), "16nm": dict(w=4500, dens=14, d0=0.07, nre_lo=2.8e6, nre_hi=100e6), "7nm": dict(w=10000, dens=22, d0=0.09, nre_lo=5.5e6, nre_hi=270e6), "5nm": dict(w=16500, dens=24, d0=0.10, nre_lo=10e6, nre_hi=480e6)}
LOGIC = {"28nm": 400, "16nm": 250, "7nm": 170, "5nm": 150}; MAXDIE = 600.0
def yld(a, d0): x = a / 100 * d0; return ((1 - math.exp(-x)) / x) ** 2
def chip(nm, mb):
    n = N[nm]; sram = mb * 8e6 / (n["dens"] * 1e6); tot = sram + LOGIC[nm]; nd = math.ceil(tot / MAXDIE); a = tot / nd
    return tot, nd, nd * n["w"] / (WA * 0.85 / a * yld(a, n["d0"]))
print("Silicon per chip (die cost only), by node and capacity")
print("%-6s %-9s %9s %5s %10s %14s" % ("node", "capacity", "mm2", "dies", "silicon $", "$ per GB of SRAM"))
for nm in N:
    for mb in (1, 64, 256, 1024):
        t, nd, c = chip(nm, mb); print("%-6s %-9s %9.0f %5d %10.1f %14.0f" % (nm, "%d MB" % mb, t, nd, c, c / (mb / 1000)))
print("\nPer-chip cost incl. 2.5x package/test/margin plus NRE spread over volume (1 GB chip); NRE low / high case")
print("%-6s %12s %12s %12s %12s" % ("node", "chip 1e3", "1e4", "1e5", "1e6"))
for nm in N:
    t, nd, c = chip(nm, 1024)
    for lab, nre in (("low", N[nm]["nre_lo"]), ("high", N[nm]["nre_hi"])):
        print("%-6s %-5s " % (nm, lab) + " ".join("%12.0f" % (2.5 * c + nre / v) for v in (1e3, 1e4, 1e5, 1e6)))
print("\nTiny recognition chip (L-class: ~4 Mb of tables incl. margin = 0.5 MB, 30 mm2 logic assumed) silicon only")
for nm in N:
    n = N[nm]; a = 0.5 * 8 / n["dens"] + 30 * {"28nm": 3, "16nm": 2, "7nm": 1.2, "5nm": 1}[nm]; c = n["w"] / (WA * 0.85 / a * yld(a, n["d0"])); print("%-6s %6.1f mm2  $%.2f per die" % (nm, a, c))
