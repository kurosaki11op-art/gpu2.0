"""Summarise an OpenROAD detailed-route DRC report: violations by type and layer, and how many lie on or next to an
SRAM macro (within 10 um of its outline) versus among the standard cells. usage: route_drc.rpt [macro_locs.txt]"""
import re, sys, collections
txt = open(sys.argv[1]).read()
viol = re.findall(r"violation type:\s*(.+?)\n.*?layer\s*(\S+).*?bbox\s*=\s*\(\s*([\d.]+),\s*([\d.]+)\s*\)\s*-\s*\(\s*([\d.]+),\s*([\d.]+)\s*\)", txt, re.S)
print("violations parsed:", len(viol))
by = collections.Counter((t.strip(), l) for t, l, *_ in viol)
for (t, l), n in by.most_common(15):
    print(f"{n:8d}  {t:30s} {l}")
if len(sys.argv) > 2:
    boxes = [tuple(map(float, ln.split())) for ln in open(sys.argv[2]) if ln.strip()]
    near = 0
    for t, l, x0, y0, x1, y1 in viol:
        cx, cy = (float(x0) + float(x1)) / 2, (float(y0) + float(y1)) / 2
        if any(a - 10 <= cx <= c + 10 and b - 10 <= cy <= d + 10 for a, b, c, d in boxes):
            near += 1
    print(f"on or within 10 um of a macro: {near} of {len(viol)} ({100 * near / max(len(viol), 1):.0f}%)")
