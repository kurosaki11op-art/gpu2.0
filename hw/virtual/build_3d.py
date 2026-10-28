"""Builds the 3D virtual board page from the simulation and synthesis results: vfpga_3d.html (a standalone document) and vfpga_3d_artifact.html (the fragment form for publishing). Reads results/synth_resources.json, results/full_testset.json, results/test_summary.json and the replay trace from the system simulation (hw/rtl/deep/out_sys.txt). Pure JavaScript canvas rendering: no external 3D library."""
import json, os
here = os.path.dirname(os.path.abspath(__file__)); R = lambda f: json.load(open(os.path.join(here, "results", f)))
dev = json.load(open(os.path.join(here, "vfpga_device.json"))); dev["grid"]["rows"] = 40
syn = R("synth_resources.json")["blocks"]; full = R("full_testset.json"); summ = R("test_summary.json")
key = {"uart": "uart (rx+tx)", "system": "L system (stage 1 + dispatcher + L Deep, 1 engine)", "forge": "L Forge tile (lane + matrix-product control)", "whole": "whole board top (UART + dispatcher + system + Forge tile)", "deep4": "L Deep, 4 parallel engines (alternative core)"}
blocks = {k: syn[v] for k, v in key.items()}
rows = [dict(name=v, **syn[v]) for k, v in key.items()]
sysm = [list(map(int, l.split())) for l in open(os.path.join(here, "..", "rtl", "deep", "out_sys.txt")) if l.strip()]
jobs = []; mm_at = {6, 14, 22}; k = 0; n = 0
while len(jobs) < 29:
    if len(jobs) in mm_at: jobs.append({"kind": "mm", "forge": 2051}); continue
    r = sysm[n]; routed = r[0]; cyc = r[12]; s1 = 4620; jobs.append({"kind": "rec", "id": n, "routed": routed, "cortex": s1, "deep": cyc - s1 if routed else 0}); n += 1
tests = [{"name": s["name"], "passed": s["passed"], "line": (s["summary"][-1] if s["summary"] else "")[:200]} for s in summ["steps"]]
finds = ["<b>A real RTL bug, found only by the full test set.</b> The final class choice read class 0 before the last table add had landed; 1 image of 10,000 got the wrong class (RTL 89.72% against 89.73%). The 300- and 200-image checks had missed it. Fixed in the system and block-RAM cores; the whole set now matches the reference.",
         "<b>Forge accumulator erased by a zero block.</b> A block whose products summed to zero but whose exponent was much larger wiped the running sum (90%-zero data: 21% error instead of 0.7%). Fixed in the lane RTL, its golden model and the tile model; exponents of all-zero blocks are now clamped.",
         "<b>The UART protocol has no flow control.</b> A host that sends the next command before the reply arrives loses bytes silently. The host script waits for each reply; the protocol note now says so.",
         "<b>No mismatches elsewhere:</b> 200,006 random lane operations, seven matrix-product data distributions, 3 stress mixes with reset injection, and a hostile UART byte stream all match their references."]
limits = "VFPGA-L1 is a simulation target sized for this design, not a real part. Resource counts come from yosys synthesis for the Gowin family; there is no place and route, timing closure or power measurement. Stage 1 is a re-implementation of the table read for the experiment's trained table, not the existing Cortex core. All cycle counts come from RTL simulation at a 50 MHz virtual clock."
data = {"device": dev, "blocks": blocks, "blockRows": rows, "split": {"cortex_logic_fraction": 0.22, "cortex_bram": 21}, "full": full, "tests": tests, "jobs": jobs, "finds": finds, "limits": limits}
t = open(os.path.join(here, "vfpga_3d.template.html")).read().replace("/*DATA*/null", json.dumps(data)); open(os.path.join(here, "vfpga_3d_artifact.html"), "w").write(t)
i = t.index("</style>") + len("</style>"); head, body = t[:i], t[i:]
open(os.path.join(here, "vfpga_3d.html"), "w").write('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n' + head + "\n</head><body>" + body + "\n</body></html>\n"); print("built vfpga_3d.html and vfpga_3d_artifact.html")
