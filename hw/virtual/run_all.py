"""Virtual device regression for the L three-layer design: runs every simulation check in sequence (never two RTL checks in the same folder at once) and writes results/test_summary.json. Steps: RTL checks of the existing blocks (L Deep three cores, the two-stage system, the layered top, the UART board top, the Forge lane and tile) and the four virtual-device tests (whole test set through the RTL, stress mix on the layered top over three seeds, Forge stress, UART board under a hostile host), then the resource fit. SIMULATED (iverilog, yosys); not a board. Usage: python run_all.py [--quick] (quick skips the 10,000-image run and the synthesis)."""
import json, os, subprocess, sys, time
here = os.path.dirname(os.path.abspath(__file__)); rtl = os.path.join(here, "..", "rtl"); month5 = os.path.join(here, "..", "brain", "experiments", "month5"); quick = "--quick" in sys.argv
STEPS = [
 ("L Deep core, asynchronous reads (300 routed images)", [sys.executable, os.path.join(rtl, "deep", "run_check_deep.py")]),
 ("L Deep core, block-RAM version (300 routed images)", [sys.executable, os.path.join(rtl, "deep", "run_check_deep.py"), "--bram"]),
 ("L Deep core, four parallel engines (300 routed images)", [sys.executable, os.path.join(rtl, "deep", "run_check_deep.py"), "--parallel"]),
 ("two-stage system with dispatcher (200 images, 38 routed)", [sys.executable, os.path.join(rtl, "deep", "run_check_system.py")]),
 ("layered top: 40 recognitions and a matrix product", [sys.executable, os.path.join(rtl, "top", "run_check_top.py")]),
 ("UART board top: 4 recognitions and a matrix product", [sys.executable, os.path.join(rtl, "top", "run_check_board.py")]),
 ("L Forge tile matrix product (16x128x16)", [sys.executable, os.path.join(month5, "forge_tile_mm_check.py")]),
 ("TEST 2: stress mix on the layered top, seed 1", [sys.executable, os.path.join(here, "run_stress_top.py"), "1"]),
 ("TEST 2: stress mix on the layered top, seed 2", [sys.executable, os.path.join(here, "run_stress_top.py"), "2"]),
 ("TEST 2: stress mix on the layered top, seed 3", [sys.executable, os.path.join(here, "run_stress_top.py"), "3"]),
 ("TEST 3: L Forge stress (200,000 lane operations, 7 data distributions)", [sys.executable, os.path.join(here, "run_stress_forge.py")]),
 ("TEST 4: UART board under a hostile host", [sys.executable, os.path.join(here, "run_stress_board.py")])]
STEPS += [("TEST 6: L Forge tile mesh, 4x4 and 8x8 tiles (distributed matrix product)", [sys.executable, os.path.join(rtl, "mesh", "mesh_run_all.py")])]
if not quick: STEPS += [("TEST 5: three stand-alone L Deep cores on every routed test image (2,001)", [sys.executable, os.path.join(here, "run_cores_testset.py"), "4"])]
if not quick: STEPS += [("TEST 1: the whole 10,000-image test set through the RTL", [sys.executable, os.path.join(here, "run_full_testset.py"), "10000", "4"]), ("resource fit on VFPGA-L1 (yosys, Gowin family)", [sys.executable, os.path.join(here, "vfpga.py")])]
out = []
for name, cmd in STEPS:
    t0 = time.time(); p = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(cmd[1])); lines = [l for l in (p.stdout + p.stderr).strip().split("\n") if l.strip()]
    rec = {"name": name, "passed": p.returncode == 0, "seconds": round(time.time() - t0, 1), "summary": lines[-3:] if p.returncode == 0 else lines[-8:]}; out.append(rec); print("%-4s %-70s %6.0fs  %s" % ("PASS" if rec["passed"] else "FAIL", name, rec["seconds"], (lines[-1] if lines else "")[:140]), flush=True)
json.dump({"steps": out, "all_passed": all(r["passed"] for r in out)}, open(os.path.join(here, "results", "test_summary.json"), "w"), indent=1); print("ALL PASSED" if all(r["passed"] for r in out) else "SOME FAILED")
