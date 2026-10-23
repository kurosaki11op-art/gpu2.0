"""L wafer-scale design: sizing model (23 Oct 2026) ESTIMATED. Paper design study, NOT a chip: how much table memory, how many tiles and what
lookup capacity a Cerebras-class wafer of tiles (one lookup core + SRAM banks + a mesh router per tile) would give at different process nodes.
Every input is an assumption stated here so it can be challenged. Cerebras WSE-3 public figures (recalled from memory, verify): 46,225 mm2, 900,000 cores,
44 GB on-chip SRAM, 21 PB/s memory bandwidth, about 23 kW, 5 nm. usage: python wafer_sizing.py"""
WAFER = 46225.0                                   # mm2 usable (WSE-3 die)
F_MEM, F_LOGIC, F_NOC, F_SPARE = 0.62, 0.10, 0.20, 0.08   # area split: memory, lookup cores, mesh + power + test, spare tiles for defects
NODES = {  # SRAM density in MB per mm2 of macro area, energy per 32-bit SRAM access (pJ), clock (GHz): ESTIMATED
    "130 nm (our open macros, measured 0.007 MB/mm2)": (0.007, 14.0, 0.05),
    "28 nm commercial": (0.6, 4.0, 0.5),
    "7 nm": (3.5, 1.5, 1.0),
    "5 nm": (4.0, 1.2, 1.0)}
BANK_MB = 0.5; TOK_LOOKUPS = 48; STEPS = 8
print("| Node | Table memory on the wafer | Banks (0.5 MB) | Peak lookups per second (every bank busy) | Memory-port power at that peak | Per-token latency across the wafer |")
print("|---|---|---|---|---|---|")
for name, (dens, e_pj, ghz) in NODES.items():
    mem_mb = WAFER * F_MEM * dens; banks = mem_mb / BANK_MB; peak = banks * ghz * 1e9
    p_w = peak * e_pj * 1e-12
    hop_ns = 2.0                                                  # per mesh hop, assumed (router + wire)
    diameter = 2 * (banks ** 0.5)                                 # mesh hops across the wafer, corner to corner
    lat_us = STEPS * 2 * diameter * hop_ns / 1000 / 2             # 8 sequential steps, request and reply, average distance about half the diameter
    print("| %s | %s | %s | %s | %.2f kW | %.1f us |" % (name, ("%.1f GB" % (mem_mb / 1024)) if mem_mb > 1024 else ("%.0f MB" % mem_mb), "{:,.0f}".format(banks), "{:.1e}".format(peak), p_w / 1e3, lat_us))
print("\nWSE-3 for scale (public, verify): 44 GB, about 23 kW. A 7 nm L wafer at the same area would hold about 2 times that memory in this model (more of the area is memory).")
