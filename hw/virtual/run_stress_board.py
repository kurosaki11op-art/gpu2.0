"""VIRTUAL DEVICE TEST 4: the UART board top under a hostile host. The byte stream contains junk before the sync byte, an invalid op code, a stray sync byte, an unknown op after valid jobs, then valid recognitions (routed and not routed, including all-zero and all-one inputs) and a matrix product; the board must ignore the junk, resynchronise and answer every valid job exactly (routed flag, prediction, cycles field, all 256 matrix outputs). SIMULATED UART model; not a board. Usage: python run_stress_board.py"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5")); import ldeep_ref as R
NB = 6176; z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); Xall = z["X"]; rr, _, _ = R.run(Xall[:2000])
img_r = Xall[int(np.nonzero(rr)[0][3])]; img_n = Xall[int(np.nonzero(rr == 0)[0][5])]; zeros = np.zeros(NB, np.uint8); ones = np.ones(NB, np.uint8)
pack = lambda b: bytes(sum(int(b[8 * k + j]) << j for j in range(8)) for k in range(NB // 8))
stream = bytearray([0x00, 0x55, 0xFF, 0x13]); jobs = []; need = {}; cum = [0]
def add(job): jobs.append(job)
def mark(n_reply_before): need[len(stream)] = cum[0]; cum[0] += n_reply_before
stream += bytes([0xA5, 0x07]); stream += bytes([0xA5, 0xA5, 0x09]); stream += bytes([0x01, 0x02])           # invalid op, double sync, stray op bytes
for name, im in (("not routed", img_n), ("routed", img_r), ("all zeros", zeros), ("all ones", ones)): mark(7); stream += bytes([0xA5, 0x01]) + pack(im); add(("rec", name, im))
mark(5 + 1280); stream += bytes([0xA5, 0x02]); add(("mm", "", None)); stream += bytes([0x77, 0xA5, 0x03]); mark(7); stream += bytes([0xA5, 0x01]) + pack(img_r); add(("rec", "routed again", img_r))
tmp = tempfile.mkdtemp(); deep = os.path.join(here, "..", "rtl", "deep"); forge = os.path.join(here, "..", "rtl", "forge"); top = os.path.join(here, "..", "rtl", "top"); board = os.path.join(here, "..", "board")
for d, names in ((deep, ["deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "l_system.v"]), (forge, ["mm_a.hex", "mm_b.hex", "mm_exp.txt", "forge_lane.v", "forge_tile_mm.v"]), (top, ["l_chip_top.v", "l_board_top.v"]), (board, ["uart_rx.v", "uart_tx.v"]), (here, ["l_board_stress_tb.v"])):
    for nme in names: shutil.copy(os.path.join(d, nme), tmp)
open(os.path.join(tmp, "host.hex"), "w").write("\n".join("%02x" % b for b in stream) + "\n"); cur = 0; lines = []
for i in range(len(stream)): cur = max(cur, need.get(i, 0)); lines.append("%08x" % cur)
open(os.path.join(tmp, "need.hex"), "w").write("\n".join(lines) + "\n")
subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "l_board_stress_tb.NHOST=%d" % len(stream), "-P", "l_board_stress_tb.WAIT_CYCLES=1500000", "l_board_stress_tb.v", "l_board_top.v", "l_chip_top.v", "l_system.v", "forge_tile_mm.v", "forge_lane.v", "uart_rx.v", "uart_tx.v"], cwd=tmp)
subprocess.check_call(["vvp", "sim"], cwd=tmp, stdout=subprocess.DEVNULL); back = bytes(int(l, 16) for l in open(os.path.join(tmp, "out_board_stress.txt")) if l.strip()); mexp = [tuple(map(int, l.split())) for l in open(os.path.join(tmp, "mm_exp.txt")) if l.strip()]
pos = 0; bad = 0; log = []
def sx(v, n): return v - (1 << n) if v >> (n - 1) else v
for kind, name, im in jobs:
    if kind == "rec":
        r = back[pos:pos + 7]; pos += 7; e_r, e_s, e_p = R.run(im[None, :]); ok = len(r) == 7 and r[0] == 0x5A and r[1] == e_r[0] and r[2] == e_p[0]; bad += (not ok); log.append("%s: %s (routed %s, class %s, cycles %s)" % (name, "ok" if ok else "MISMATCH", r[1] if len(r) > 1 else "?", r[2] if len(r) > 2 else "?", int.from_bytes(r[3:7], "little") if len(r) == 7 else "?"))
    else:
        h = back[pos:pos + 5]; pos += 5; body = back[pos:pos + 1280]; pos += 1280; got = [(sx(int.from_bytes(body[5 * k:5 * k + 3], "little"), 24), sx(int.from_bytes(body[5 * k + 3:5 * k + 5], "little"), 16)) for k in range(len(body) // 5)]; ok = len(h) == 5 and h[0] == 0x5B and got == mexp; bad += (not ok); log.append("matrix product: %s (%d outputs, cycles %d)" % ("ok" if ok else "MISMATCH", len(got), int.from_bytes(h[1:5], "little") if len(h) == 5 else -1))
extra = len(back) - pos; print("\n".join(log)); print("bytes back %d, expected %d (extra bytes from junk: %d); failures %d" % (len(back), pos, extra, bad)); shutil.rmtree(tmp); sys.exit(1 if (bad or extra) else 0)
