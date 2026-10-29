"""29 Oct 2026, ESTIMATED (every energy is a model from the project's constants, none measured). Fixes two limits of cascade_test.py: (1) the CNN energies counted multiplies only; here weight reads and activation traffic are added, in three cases;
(2) the chip's first-stage energy is uncertain (49 nJ by operation count; the Cortex layout estimate is 20 to 28 times its operation count), so the break-even first-stage energy is computed: how much worse can the chip be before the cascade stops winning.
Constants: int8 multiply-add 0.2 pJ (Horowitz 45 nm reference); SRAM read 10 pJ per 64-bit word up to 8 KB, about 22 pJ per word at 50 KB (project model); large on-chip SRAM 0.495 to 2.78 pJ per bit (memory-technology study, MODELLED), i.e. 4 to 22 pJ per byte.
Parameters/activations counted from the two reference networks in cnn_confidence.py (int8 assumed). Accuracies from cascade_test.log."""
MAC = 0.2e-6   # uJ per multiply-add
small = dict(macs=3.87e6, params=50.2e3, acts=(25088 + 6272 + 12544 + 3136)); strong = dict(macs=19.0e6, params=(320 + 9248 + 18496 + 36928 + 802_816 + 2570), acts=(25088 * 2 + 6272 + 12544 * 2 + 3136 + 256))
def energy(n, case):
    e = n["macs"] * MAC; act = n["acts"] * 2 * (10 / 8) * 1e-6          # each activation written and read once, small-SRAM 10 pJ per 8 bytes
    if case == "multiplies only": return e
    if n is small: w = n["params"] / 8 * 22e-6                             # 50 KB: 22 pJ per word
    elif case == "traffic, weights amortised over a batch of 64": w = n["params"] * 12e-6 / 64
    elif case == "traffic, batch 1, large SRAM (4 pJ/byte)": w = n["params"] * 4e-6
    else: w = n["params"] * 22e-6
    return e + act + w
cases = ["multiplies only", "traffic, weights amortised over a batch of 64", "traffic, batch 1, large SRAM (4 pJ/byte)", "traffic, batch 1, large SRAM (22 pJ/byte)"]
print("%-48s %12s %12s" % ("CNN energy per image (uJ)", "small CNN", "strong CNN"))
for c in cases: print("%-48s %12.2f %12.2f" % (c, energy(small, c), energy(strong, c)))
f, E_CHIP = 0.15, 0.049
print("\\nCascade at 15%% flagged (accuracy: chip -> strong 91.42%%, small -> strong 91.79%%, strong alone 91.75%%), chip first stage %.3f uJ:" % E_CHIP)
print("%-48s %14s %18s %16s" % ("case", "chip cascade", "small->strong", "strong alone"))
for c in cases:
    Es, Em = energy(strong, c), energy(small, c); print("%-48s %11.2f uJ %15.2f uJ %13.2f uJ  (%.1fx less than strong alone, %.1fx less than small->strong)" % (c, E_CHIP + f * Es, Em + f * Es, Es, Es / (E_CHIP + f * Es), (Em + f * Es) / (E_CHIP + f * Es)))
print("\\nBreak-even first-stage energy of the chip at 15% flagged (above it the chip cascade loses): vs strong alone = (1 - f) x strong; vs small->strong = small CNN energy")
for c in cases: print("%-48s vs strong alone %.2f uJ (%.0fx the 49 nJ estimate) | vs small->strong %.2f uJ (%.0fx)" % (c, (1 - f) * energy(strong, c), (1 - f) * energy(strong, c) / E_CHIP, energy(small, c), energy(small, c) / E_CHIP))
