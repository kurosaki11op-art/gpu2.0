"""Virtual FPGA device VFPGA-L1 (vfpga_device.json): resource model and fit check. Synthesises each block of the L design for the Gowin family with yosys (the vendor family the project targets), counts the primitives it uses (LUT4, carry cells, flip-flops, 18 Kbit block RAM, 9x9 multipliers) and checks them against the virtual device's budget. The device is a SIMULATION TARGET sized for this design, not a real part; the counts are yosys estimates, not place-and-route results (no timing closure is checked). Usage: python vfpga.py   (writes results/synth_resources.json, takes several minutes)."""
import json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
here = os.path.dirname(os.path.abspath(__file__)); rtl = os.path.join(here, "..", "rtl"); board = os.path.join(here, "..", "board"); dev = json.load(open(os.path.join(here, "vfpga_device.json")))
BLOCKS = {  # name: (top module, source files, hex files)
 "uart (rx+tx)": ("uart_pair", [here + "/uart_pair.v", board + "/uart_rx.v", board + "/uart_tx.v"], []),
 "L system (stage 1 + dispatcher + L Deep, 1 engine)": ("l_system", [rtl + "/deep/l_system.v"], ["deep_wcode1", "deep_wcode", "deep_wcl", "deep_hdr", "deep_lits"]),
 "L Deep, 4 parallel engines (alternative core)": ("ldeep_core_p", [rtl + "/deep/ldeep_core_p.v"], [f"deep_{k}_e{e}" for k in ("wcode", "wcl", "hdr", "lits") for e in range(4)]),
 "L Forge tile (lane + matrix-product control)": ("forge_tile_mm", [rtl + "/forge/forge_lane.v", rtl + "/forge/forge_tile_mm.v"], ["mm_a", "mm_b"]),
 "whole board top (UART + dispatcher + system + Forge tile)": ("l_board_top", [rtl + "/top/l_board_top.v", rtl + "/top/l_chip_top.v", rtl + "/deep/l_system.v", rtl + "/forge/forge_lane.v", rtl + "/forge/forge_tile_mm.v", board + "/uart_rx.v", board + "/uart_tx.v"], ["deep_wcode1", "deep_wcode", "deep_wcl", "deep_hdr", "deep_lits", "mm_a", "mm_b"])}
def synth(name):
    top, srcs, hexes = BLOCKS[name]; t = tempfile.mkdtemp()
    for h in hexes: shutil.copy(os.path.join(rtl, "deep" if h.startswith("deep") else "forge", h + ".hex"), t)
    files = " ".join(srcs); subprocess.run(["yowasp-yosys", "-q", "-p", "read_verilog -sv %s; synth_gowin -top %s -noabc9; tee -o stat.txt stat" % (files, top)], cwd=t, capture_output=True, timeout=1500)
    txt = open(os.path.join(t, "stat.txt")).read(); shutil.rmtree(t); sec = txt[txt.rindex("cells"):] if "cells" in txt else txt
    cnt = lambda pat: sum(int(m.group(1)) for m in re.finditer(r"^\s+(\d+)\s+(?:%s)\s*$" % pat, sec, re.M))
    return {"lut4": cnt("LUT[1-4]"), "alu": cnt("ALU"), "ff": cnt("DFF[A-Z]*"), "bsram_18k": cnt("SPX9|DPB|SDPB|SP|SDPX9|DPX9B"), "mult9x9": cnt("MULT9X9")}
if __name__ == "__main__":
    only = sys.argv[1:] or list(BLOCKS)
    with ThreadPoolExecutor(3) as ex: res = dict(zip(only, ex.map(synth, only)))
    out = {"device": dev["name"], "budget": {k: dev[k] for k in ("lut4", "alu", "ff", "bsram_18k", "mult9x9")}, "blocks": res}; json.dump(out, open(os.path.join(here, "results", "synth_resources.json"), "w"), indent=1)
    print("%-62s %8s %7s %7s %6s %6s" % ("block", "LUT4", "ALU", "FF", "BRAM", "MULT"))
    for n, r in res.items(): print("%-62s %8d %7d %7d %6d %6d" % (n, r["lut4"], r["alu"], r["ff"], r["bsram_18k"], r["mult9x9"]))
    b = res.get("whole board top (UART + dispatcher + system + Forge tile)")
    if b:
        print("\nFIT of the whole board top on %s (logic = LUT4 + carry cells):" % dev["name"])
        for k, lab in (("lut4", "LUT4"), ("alu", "carry cells"), ("ff", "flip-flops"), ("bsram_18k", "block RAM 18 Kbit"), ("mult9x9", "9x9 multipliers")): print("  %-20s %6d of %6d  (%4.1f%%)" % (lab, b[k], dev[k], 100 * b[k] / dev[k]))
        print("  logic cells (LUT4 + carry): %d of %d (%.1f%%)" % (b["lut4"] + b["alu"], dev["lut4"], 100 * (b["lut4"] + b["alu"]) / dev["lut4"]))
