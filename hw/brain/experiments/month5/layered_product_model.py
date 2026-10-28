"""28 Oct 2026, ESTIMATED. LAYERED PRODUCT LINE MODEL (founder's idea: build separate layers -- L Cortex, L Deep, dense-matrix, physics, rendering, big memory -- and give each customer only the layers they need, supplying memory and power only to those). Compares, for five customer products, (i) one universal die with everything, (ii) a custom monolithic die per product, (iii) a chiplet kit where each layer is designed once and combined. Node 16 nm class (wafer 4500 USD, SRAM 14 Mb/mm2, D0 0.07/cm2: same ASSUMED/REFERENCE inputs as cost_by_node.py). Layer logic areas and memory sizes are our ASSUMPTIONS. Chiplet overheads ASSUMED: +10% area per chiplet for die-to-die links, 20 USD packaging per extra chiplet, link energy not modelled. NRE: mask 1.5M per distinct die design (aggregator low case), logic design cost per mm2 of NEW logic: 'IBS-like' 0.3M, 'lean' 0.03M (both ASSUMED); SRAM macros are licensed IP, no design cost. Volume: 10,000 chips per product. Price = 2.5 x silicon + packaging + NRE/volume."""
import math
WA = math.pi * 150 ** 2; W16 = 4500; DENS = 14; D0 = 0.07; MAXDIE = 600.0; LEAK = 60e-12
L = {"Cortex": (0.5, 30), "Deep": (4, 40), "Dense": (64, 90), "Physics": (256, 110), "Render": (256, 100), "Mem1GB": (1024, 10)}   # (SRAM MB, logic mm2)
P = {"A edge sensor": ["Cortex"], "B assistant": ["Cortex", "Deep"], "C vision+language server": ["Cortex", "Deep", "Dense", "Mem1GB"], "D science": ["Physics", "Dense", "Mem1GB"], "E everything": list(L)}
def yld(a): x = a / 100 * D0; return ((1 - math.exp(-x)) / x) ** 2
def die(a): return W16 / (WA * 0.85 / a * yld(a))
def area(names, ovh=1.0): return sum(L[n][0] * 8 / DENS + L[n][1] for n in names) * ovh
def silicon(a): nd = math.ceil(a / MAXDIE); return nd * die(a / nd), nd
def leak(names): return sum(L[n][0] for n in names) * 8e6 * LEAK
V = 10000
for dname, dpm in (("IBS-like design cost 0.3M per new logic mm2", 0.3e6), ("lean design cost 0.03M per mm2", 0.03e6)):
    print("\n=== %s ; volume %d per product ===" % (dname, V))
    nre_block = {n: 1.5e6 + dpm * L[n][1] for n in L}
    allnames = list(L); ua = area(allnames); us, und = silicon(ua); unre = 1.5e6 * und + dpm * sum(L[n][1] for n in L); uprice = 2.5 * us + unre / (V * len(P))
    print("universal die (everything for everyone): %.0f mm2, %d dies, silicon $%.0f, price/chip $%.0f (volume %d), idle leakage if all memory powered %.2f W" % (ua, und, us, uprice, V * len(P), leak(allnames)))
    print("%-26s %10s %12s %12s %12s %10s" % ("product", "needs mm2", "custom mono $", "chiplet kit $", "universal $", "leak W"))
    tot_chip_nre = sum(nre_block.values())
    for pn, names in P.items():
        a = area(names); s1, nd = silicon(a); cust_nre = 1.5e6 * nd + dpm * sum(L[n][1] for n in names); custom = 2.5 * s1 + cust_nre / V
        parts = sum(die(area([n], 1.1)) for n in names) if all(area([n], 1.1) <= MAXDIE for n in names) else sum(silicon(area([n], 1.1))[0] for n in names); kit = 2.5 * parts + 20 * len(names) + (tot_chip_nre / len(P)) / V
        print("%-26s %10.0f %12.0f %12.0f %12.0f %10.2f" % (pn, a, custom, kit, uprice, leak(names)))
    print("NRE: universal %.1fM | all five custom dies %.1fM | chiplet kit (each layer once) %.1fM" % (unre / 1e6, sum(1.5e6 * silicon(area(n))[1] + dpm * sum(L[x][1] for x in n) for n in P.values()) / 1e6, tot_chip_nre / 1e6))
