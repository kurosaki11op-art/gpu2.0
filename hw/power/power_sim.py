"""Switching-activity power simulation of the SPARK RTL (pre-silicon power estimation).

Runs the real Verilog (iverilog) on real text, records a VCD window (after warm-up), and counts
  - data toggles: every bit flip of every net/register in the design (clock excluded)
  - memory accesses: new read address on each RAM (block RAM vs small LUT RAM), and writes
  - clock cycles (clock-tree power: every flip-flop is clocked every cycle; no clock gating)
then converts them to energy with stated per-event energies (45 nm class, Horowitz ISSCC 2014 scale):
  E_TOGGLE = 2 fJ per net bit-toggle (~3 fF at 1.1 V)
  E_BRAM   = 5 pJ per 32-bit block-RAM access (8 KB SRAM read, Horowitz) ; E_LRAM = 0.06 pJ/bit small RAM
  E_CLK    = 2 fJ per flip-flop per cycle, 4,090 flip-flops (from place-and-route)
Two memory policies: "as built" (block RAMs are clocked/read every cycle) and "read-enable"
(a block RAM only spends energy when its address changes: a one-line RTL change).
Usage: python3 power_sim.py   (writes power_results.json)
"""
import json, os, re, shutil, subprocess, sys
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
E_TOGGLE, E_BRAM, E_LRAM_BIT, E_CLK_FF, N_FF = 2e-3, 5.0, 0.06, 2e-3, 4090   # pJ
BRAMS = ("u_emb", "u_emb1", "u_emb2", "u_w0", "u_w1", "u_w2", "u_w3", "u_tab_tag", "u_tab_dat")
FROM, N = 240, 60
CONFIGS = {
    "dense (compute every neuron, GPU-style)": "+sparse=0",
    "event-driven (skip silent neurons)": "+sparse=1",
    "SPARK effort LOW": "+sparse=1 +adapt=1 +exit=1 +exit_th=2 +recall=1 +conf_th=0 +rmode=0",
    "SPARK effort MEDIUM": "+sparse=1 +adapt=1 +exit=1 +exit_th=2 +recall=1 +conf_th=0 +rmode=1",
    "SPARK effort HIGH": "+sparse=1 +adapt=1 +exit=1 +exit_th=2 +recall=1 +conf_th=0 +rmode=2 +arb_th=128",
}


def parse_vcd(path):
    ids, scope = {}, []
    width = {}
    last = {}
    tog = 0
    acc = {}          # ram instance -> address changes (reads)
    wr = {}           # ram instance -> write-enable high samples (approx writes)
    ram_ra = {}       # id -> ram instance (read address)
    t0 = t1 = None
    clk_id = None
    with open(path) as f:
        for line in f:
            if line.startswith("$enddefinitions"):
                break
            p = line.split()
            if not p:
                continue
            if p[0] == "$scope":
                scope.append(p[2])
            elif p[0] == "$upscope":
                scope.pop()
            elif p[0] == "$var":
                w, i, name = int(p[2]), p[3], p[4]
                if i in width:
                    continue
                width[i] = w
                if name == "clk" and clk_id is None:
                    clk_id = i
                inst = scope[-1] if scope else ""
                if inst.startswith("u_") and name in ("ra", "a"):
                    if inst.startswith("u_tab") and name != "a":
                        continue
                    if not inst.startswith("u_tab") and name != "ra":
                        continue
                    ram_ra[i] = inst
        for line in f:
            c = line[0]
            if c == "#":
                t = int(line[1:])
                if t0 is None:
                    t0 = t
                t1 = t
                continue
            if c == "b":
                v, i = line[1:].split()
            elif c in "01xzXZ":
                v, i = c, line[1:].strip()
            else:
                continue
            if i == clk_id:
                continue
            v = v.replace("x", "0").replace("z", "0").replace("X", "0").replace("Z", "0")
            w = width.get(i, 1)
            old = last.get(i)
            nv = int(v, 2)
            if old is not None:
                tog += bin(old ^ nv).count("1")
                if i in ram_ra and old != nv:
                    acc[ram_ra[i]] = acc.get(ram_ra[i], 0) + 1
            last[i] = nv
    cycles = (t1 - t0) / 10000.0   # timescale 1ns/1ps, 10 ns clock
    return tog, acc, cycles


RAMW = {"u_acc0": 128, "u_acc1": 128, "u_acc2": 128, "u_acc3": 128, "u_h0": 128, "u_h1": 128,
        "u_th0": 128, "u_th1": 128}


def run(item):
    name, args = item
    d = os.path.join(HERE, "run_" + re.sub(r"[^a-z]+", "_", name.lower())[:30])
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(os.path.join(HERE, "tmpl"), d)
    subprocess.run(f"vvp -n sim.vvp {args} +thr=1 +n={FROM + N} +dump_from={FROM} +dump_n={N}",
                   shell=True, cwd=d, check=True, capture_output=True)
    rows = [list(map(int, l.split())) for l in open(os.path.join(d, "rtl_out.txt"))][FROM:FROM + N]
    tog, acc, cycles = parse_vcd(os.path.join(d, "act.vcd"))
    os.remove(os.path.join(d, "act.vcd"))
    bram_acc = sum(v for k, v in acc.items() if k in BRAMS)
    lram_bits = sum(v * RAMW.get(k, 32) for k, v in acc.items() if k not in BRAMS)
    e_tog = tog * E_TOGGLE
    e_clk = cycles * N_FF * E_CLK_FF
    e_lram = lram_bits * E_LRAM_BIT
    e_bram_re = bram_acc * E_BRAM
    e_bram_built = cycles * len(BRAMS) * E_BRAM
    return dict(config=name, tokens=N, cycles_per_token=cycles / N,
                rtl_tok_cycles=sum(r[10] for r in rows) / N,
                toggles_per_token=tog / N, bram_accesses_per_token=bram_acc / N,
                nJ_toggle=e_tog / N / 1e3, nJ_clock=e_clk / N / 1e3, nJ_small_ram=e_lram / N / 1e3,
                nJ_bram_read_enable=e_bram_re / N / 1e3, nJ_bram_as_built=e_bram_built / N / 1e3,
                nJ_total_read_enable=(e_tog + e_clk + e_lram + e_bram_re) / N / 1e3,
                nJ_total_as_built=(e_tog + e_clk + e_lram + e_bram_built) / N / 1e3)


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(run, CONFIGS.items()))
    d = res[0]
    for r in res:
        r["x_less_read_enable"] = d["nJ_total_read_enable"] / r["nJ_total_read_enable"]
        r["x_less_as_built"] = d["nJ_total_as_built"] / r["nJ_total_as_built"]
        r["x_less_toggles"] = d["toggles_per_token"] / r["toggles_per_token"]
        print(f"{r['config']:42s} cycles {r['cycles_per_token']:7.0f}  toggles {r['toggles_per_token']:9.0f}  "
              f"BRAM acc {r['bram_accesses_per_token']:6.0f}  E(read-en) {r['nJ_total_read_enable']:6.1f} nJ "
              f"({r['x_less_read_enable']:.1f}x)  E(as built) {r['nJ_total_as_built']:6.1f} nJ ({r['x_less_as_built']:.1f}x)",
              flush=True)
    json.dump(res, open(os.path.join(HERE, "power_results.json"), "w"), indent=2)
