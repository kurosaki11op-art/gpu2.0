"""Summarise an OpenROAD detailed-route DRC report (format: 'violation type: T / srcs: ... / bbox = ( x0, y0 ) - ( x1, y1 ) on
Layer L'): violations by type and layer, and how many lie within 10 um of an SRAM macro outline, and how many of the
shorts / spacing errors involve power nets. usage: route_drc.rpt [macro_locs.txt]"""
import re, sys, collections
txt = open(sys.argv[1]).read()
viol = re.findall(r"violation type:\s*(.+?)\n\s*srcs:\s*(.*?)\n\s*bbox = \(\s*([\d.]+),\s*([\d.]+)\s*\)\s*-\s*\(\s*([\d.]+),\s*([\d.]+)\s*\)\s*on Layer (\S+)", txt)
print("violations parsed:", len(viol))
by = collections.Counter((t.strip(), l) for t, _, _, _, _, _, l in viol)
for (t, l), n in by.most_common(20):
    print(f"{n:8d}  {t:24s} {l}")
bt = collections.Counter(t.strip() for t, *_ in viol)
print("by type:", dict(bt.most_common()))
pw = sum(1 for _, s, *_ in viol if re.search(r"VPWR|VGND|VDD|VSS|vccd|vssd", s))
print(f"involving a power net: {pw} of {len(viol)}")
if len(sys.argv) > 2:
    boxes = [tuple(map(float, ln.split())) for ln in open(sys.argv[2]) if ln.strip()]
    near = 0
    for _, _, x0, y0, x1, y1, _ in viol:
        cx, cy = (float(x0) + float(x1)) / 2, (float(y0) + float(y1)) / 2
        if any(a - 10 <= cx <= c + 10 and b - 10 <= cy <= d + 10 for a, b, c, d in boxes):
            near += 1
    print(f"on or within 10 um of a macro: {near} of {len(viol)} ({100 * near / max(len(viol), 1):.0f}%)")
