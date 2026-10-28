"""Check of the UART board top (l_board_top.v) with a UART model standing in for the PC: 4 recognitions (routed flag and prediction against sys_exp.txt, header bytes) and one matrix product (all 256 outputs against mm_exp.txt). SIMULATED; not run on a board. 28 Oct 2026."""
import os, shutil, subprocess, sys, tempfile
here = os.path.dirname(os.path.abspath(__file__)); deep = os.path.join(here, "..", "deep"); forge = os.path.join(here, "..", "forge"); board = os.path.join(here, "..", "..", "board"); tmp = tempfile.mkdtemp()
for d, names in ((deep, ["deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "sys_in.hex", "sys_exp.txt", "l_system.v"]), (forge, ["mm_a.hex", "mm_b.hex", "mm_exp.txt", "forge_lane.v", "forge_tile_mm.v"]), (board, ["uart_rx.v", "uart_tx.v"]), (here, ["l_chip_top.v", "l_board_top.v", "l_board_tb.v"])):
    for nme in names: shutil.copy(os.path.join(d, nme), tmp)
allexp = [list(map(int, l.split())) for l in open(os.path.join(tmp, "sys_exp.txt")) if l.strip()]; rt = [i for i, e in enumerate(allexp) if e[0] == 1][:2]; nr = [i for i, e in enumerate(allexp) if e[0] == 0][:2]; pick = [nr[0], rt[0], nr[1], rt[1]]
open(os.path.join(tmp, "board_idx.hex"), "w").write("\n".join("%04x" % i for i in pick) + "\n")
subprocess.check_call(["iverilog", "-g2012", "-o", "board_sim", "l_board_tb.v", "l_board_top.v", "l_chip_top.v", "l_system.v", "forge_tile_mm.v", "forge_lane.v", "uart_rx.v", "uart_tx.v"], cwd=tmp); subprocess.check_call(["timeout", "2400", "vvp", "board_sim"], cwd=tmp, stdout=subprocess.DEVNULL)
lines = [list(map(int, l.split())) for l in open(os.path.join(tmp, "out_board.txt")) if l.strip()]; rec = lines[:4]; mm = lines[4:]
exp = [allexp[i] for i in pick]; mexp = [tuple(map(int, l.split())) for l in open(os.path.join(tmp, "mm_exp.txt")) if l.strip()]
bad_r = sum(1 for e, g in zip(exp, rec) if not (g[0] == 0x5A and g[1] == e[0] and g[2] == e[-1])); hdr = mm[0]; cyc = hdr[1] | hdr[2] << 8 | hdr[3] << 16 | hdr[4] << 24
dec = lambda b: (b[0] | b[1] << 8 | b[2] << 16 if not (b[2] & 128) else (b[0] | b[1] << 8 | b[2] << 16) - (1 << 24), (b[3] | b[4] << 8) - (1 << 16) if b[4] & 128 else (b[3] | b[4] << 8))
got = [dec(l) for l in mm[1:]]; bad_m = sum(1 for e, g in zip(mexp, got) if e != g)
print("recognitions %d: reply mismatches %d (cycles reported %s); matrix product: header %s, %d outputs, mismatches %d, tile cycles %d" % (len(rec), bad_r, [g[3] | g[4] << 8 | g[5] << 16 | g[6] << 24 for g in rec], "ok" if hdr[0] == 0x5B else "bad", len(got), bad_m, cyc))
shutil.rmtree(tmp); sys.exit(1 if (bad_r or bad_m or len(got) != 256 or hdr[0] != 0x5B) else 0)
