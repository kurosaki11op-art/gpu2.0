"""28 Oct 2026, ESTIMATED. ONE CHIP, THREE LAYERS (L Cortex + L Deep + shared memory block, on one die, power-gated layers) -- memory map, die area by process, and energy per operation with banking and gating. Real numbers from this repo (SKY130 layout, hw/results/cortex_asic_estimate.md): Cortex memory 84 KB in 63 OpenRAM 2 KB macros = 0.285 mm2 each (7 KB/mm2), logic 0.84 mm2, 0.18-0.26 uJ per decision in its own layout (ESTIMATED), operation count 9.4 nJ. L Deep sizes from docs/L_accelerator_design.md (MODELLED: ternary weights 227 KB at d=128 or 510 KB at d=192; delta-rule state 32/72 KB). ASSUMED: shared block 256 KB, Deep logic 2 mm2 at 130 nm, density per node, energy constants (Horowitz 45 nm SRAM read: 10 pJ per 64-bit word at 8 KB, 20 at 32 KB, rising to 100 at 1 MB)."""
mem = {"Cortex (table+dream counts+list, layout)": 84, "Deep weights ternary d=128": 227, "Deep state (delta rule + scan + conv)": 35, "shared block (embeddings, buffers, replay store) ASSUMED": 256}
tot = sum(mem.values()); print("MEMORY MAP (KB):"); [print("  %-60s %5d" % kv) for kv in mem.items()]; print("  %-60s %5d  (d=192 Deep: %d)" % ("total", tot, tot + (510 - 227) + (72 - 35)))
KB_PER_MM2 = {"SKY130 open macros (measured in our layout)": 7.0, "SKY130 denser compiler (ASSUMED 4x)": 28.0, "28 nm (ASSUMED 7 Mb/mm2)": 875.0, "16 nm (ASSUMED 14 Mb/mm2)": 1750.0}
LOGIC_130 = 0.84 + 2.0; SCALE = {"SKY130": 1.0, "28 nm": (28 / 130) ** 2 * 2, "16 nm": (16 / 130) ** 2 * 2}
print("\nDIE AREA (mm2) for the %d KB map + logic, by process:" % tot)
for nm, d in KB_PER_MM2.items():
    k = "SKY130" if "SKY130" in nm else "28 nm" if "28" in nm else "16 nm"; a = tot / d + LOGIC_130 * SCALE[k]; print("  %-48s memory %7.1f + logic %5.2f = %7.1f mm2" % (nm, tot / d, LOGIC_130 * SCALE[k], a))
sram = lambda kb: 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
words = 227 * 1024 / 8; ops = 0.907e6
print("\nDEEP, ENERGY PER TOKEN (45 nm constants, ESTIMATED; every ternary weight read once per token, dense case):")
for lab, bank in (("one 227 KB array", 227), ("32 KB banks", 32), ("8 KB banks (wake one bank at a time)", 8)):
    e = words * sram(bank) / 1000 + ops * 0.03 / 1000; print("  %-40s %6.2f nJ/token (reads %.2f + adds %.3f)" % (lab, e, words * sram(bank) / 1000, ops * 0.03 / 1000))
print("  with event skipping, 5%% FFN neurons fire (saves 31%% of adds and reads, design doc): %.1f nJ (8 KB banks)" % (0.69 * (words * 10 / 1000 + ops * 0.03 / 1000)))
print("\nCORTEX, ENERGY PER DECISION: operation count 9.4 nJ | own layout 0.18-0.26 uJ (20-28x above) -> the pitch figure must be the layout one until the gap is closed")
print("\nSYSTEM, average per task with a router: Cortex always on, Deep woken on a share r of tasks (r from the routed-pass results: 0.2 earlier for images; for language the share is unknown)")
for r in (0.05, 0.2, 1.0): print("  r=%.2f: Cortex 0.22 uJ + r x Deep 0.32 uJ (8KB banks, 1 token) = %.2f uJ" % (r, 0.22 + r * 0.318))
