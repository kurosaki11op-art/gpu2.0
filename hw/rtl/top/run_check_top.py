"""Check of the top-level dispatcher (hw/rtl/top/l_chip_top.v): 40 recognitions (routed flag, scores, prediction against sys_exp.txt) and one Forge matrix product (against the lane golden model), and the cycles each layer is awake. Copies the hex files into a temporary folder, so it does not touch the deep and forge folders. 28 Oct 2026."""
import os, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); deep = os.path.join(here, "..", "deep"); forge = os.path.join(here, "..", "forge"); tmp = tempfile.mkdtemp()
for d, names in ((deep, ["deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "sys_in.hex", "sys_exp.txt", "l_system.v"]), (forge, ["mm_a.hex", "mm_b.hex", "mm_exp.txt", "forge_lane.v", "forge_tile_mm.v"]), (here, ["l_chip_top.v", "l_chip_tb.v"])):
    for nme in names: shutil.copy(os.path.join(d, nme), tmp)
subprocess.check_call(["iverilog", "-g2012", "-o", "top_sim", "l_chip_tb.v", "l_chip_top.v", "l_system.v", "forge_tile_mm.v", "forge_lane.v"], cwd=tmp); subprocess.check_call(["timeout", "1500", "vvp", "top_sim"], cwd=tmp, stdout=subprocess.DEVNULL)
out = [l.split() for l in open(os.path.join(tmp, "out_top.txt")) if l.strip()]; rec = [list(map(int, l[1:])) for l in out if l[0] == "R"]; mm = [tuple(map(int, l[1:])) for l in out if l[0] == "M"]; act = [l for l in out if l[0] == "ACTIVE"][0]
exp = [list(map(int, l.split())) for l in open(os.path.join(tmp, "sys_exp.txt")) if l.strip()][:len(rec)]; mexp = [tuple(map(int, l.split())) for l in open(os.path.join(tmp, "mm_exp.txt")) if l.strip()]
bad_r = sum(1 for e, g in zip(exp, rec) if e != g); bad_m = sum(1 for e, g in zip(mexp, mm) if e != g)
print("recognitions %d (routed %d): mismatches %d; matrix product outputs %d: mismatches %d; cycles awake: cortex %s, deep %s, forge %s, total %s" % (len(rec), sum(e[0] for e in exp), bad_r, len(mm), bad_m, act[2], act[4], act[6], act[8]))
shutil.rmtree(tmp); sys.exit(1 if (bad_r or bad_m or len(mm) != len(mexp)) else 0)
