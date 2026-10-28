"""Splits the L Deep memories into P engine slices (contiguous code-row range and interleaved clauses (clause c to engine c mod P, since clauses are ranked by use and the first ones are longest) per engine) for ldeep_core_p.v. Reads deep_wcode.hex, deep_wcl.hex, deep_hdr.hex, deep_lits.hex; writes deep_*_e<k>.hex and deep_part.txt. 28 Oct 2026. Usage: python partition_engines.py [P]"""
import os, sys
P = int(sys.argv[1]) if len(sys.argv) > 1 else 4; os.chdir(os.path.dirname(os.path.abspath(__file__)))
rd = lambda f: [l.strip() for l in open(f) if l.strip()]
wcode, wcl, hdr, lits = rd("deep_wcode.hex"), rd("deep_wcl.hex"), rd("deep_hdr.hex"), rd("deep_lits.hex"); NCODE, NCL = len(wcode), len(wcl)
cb = [NCODE * e // P for e in range(P + 1)]; cc = [NCL * e // P for e in range(P + 1)]; info = []
for e in range(P):
    open("deep_wcode_e%d.hex" % e, "w").write("\n".join(wcode[cb[e]:cb[e + 1]]) + "\n"); mine = [c for c in range(NCL) if c % P == e]; open("deep_wcl_e%d.hex" % e, "w").write("\n".join(wcl[c] for c in mine) + "\n")
    hh = []; ll = []
    for c in mine:
        s, n = int(hdr[c][:4], 16), int(hdr[c][4:], 16); hh.append("%04x%02x" % (len(ll), n)); ll.extend(lits[s:s + n])
    open("deep_hdr_e%d.hex" % e, "w").write("\n".join(hh) + "\n"); open("deep_lits_e%d.hex" % e, "w").write("\n".join(ll) + "\n"); info.append((cb[e], cb[e + 1] - cb[e], len(mine), len(ll)))
open("deep_part.txt", "w").write("P %d\n" % P + "\n".join("engine %d: code base %d count %d, clauses %d, literals %d" % ((e,) + info[e]) for e in range(P)) + "\n"); print(open("deep_part.txt").read())
