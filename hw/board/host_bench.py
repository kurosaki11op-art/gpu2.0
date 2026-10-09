#!/usr/bin/env python3
"""SPARK on Tang Nano 20K -- host benchmark driver.

Talks to spark_board_top over the BL616 USB-UART (protocol in spark_board_top.v),
streams a text file through the core one byte ("token") at a time, records
pred / path / tok_cycles / wall time per token and, optionally, reads the
ESP32 + INA219 power log from a second serial port to compute energy per token.

Examples
  # no hardware: golden model stands in for the FPGA, power is SIMULATED
  python3 hw/board/host_bench.py --dry-run --repeats 2 --idle-s 0.5
  # board only (timing + cycles + golden check)
  python3 hw/board/host_bench.py --port /dev/ttyUSB1
  # board + power logger
  python3 hw/board/host_bench.py --port /dev/ttyUSB1 --power-port /dev/ttyUSB0 \
      --text sample.py --idle-s 10 --repeats 5 --ambient-c 23.5

Outputs (in --out, default hw/results/board_<timestamp>/):
  runs.csv     one row per (config, repeat)
  tokens.csv   one row per token
  summary.md   mean +- std over repeats per config

Energy per token
  E_total = P_avg_run * T_run / N                (whole board, incl. BL616, LEDs, regulators)
  E_above = (P_avg_run - P_idle) * T_run / N     (above the idle baseline of the same config)
  P_idle is measured just before each repeat for --idle-s seconds with the
  board configured but no tokens running. The "uart-control" pseudo-config sends
  pings at the same rate as tokens (no inference) so the cost of the UART/USB
  traffic itself can be subtracted: E_core ~= E_above(config) - E_above(uart-control).

Note on state: the core keeps its context, recall table and accumulators across
tokens AND across config changes (only a bitstream reload clears them). The
golden check mirrors that by keeping one model object and swapping its config,
so the check stays exact as long as this script is the only thing that has
talked to the board since it was programmed. Use --no-check otherwise.
"""
import argparse
import csv
import math
import os
import queue
import statistics
import struct
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))

CLK_HZ = 27_000_000
ESP_COLS = ["t_ms", "t_us", "bus_V", "shunt_mV", "current_mA", "power_mW", "trig", "mark"]

# name -> (flags dict, cap, exit_th, conf_th)
CONFIGS = {
    "dense":      dict(sparse=0, delta=0, exit_en=0, recall=0, adapt=0, cap=0, exit_th=64, conf_th=1),
    "event":      dict(sparse=1, delta=0, exit_en=0, recall=0, adapt=0, cap=0, exit_th=64, conf_th=1),
    "event+delta": dict(sparse=1, delta=1, exit_en=0, recall=0, adapt=0, cap=0, exit_th=64, conf_th=1),
    "event+exit": dict(sparse=1, delta=0, exit_en=1, recall=0, adapt=0, cap=0, exit_th=64, conf_th=1),
    "event+recall": dict(sparse=1, delta=0, exit_en=0, recall=1, adapt=0, cap=0, exit_th=64, conf_th=1),
    "adaptive":   dict(sparse=1, delta=0, exit_en=1, recall=1, adapt=1, cap=0, exit_th=64, conf_th=1),
    "uart-control": None,   # pings only: measures UART/USB traffic cost
}
DEFAULT_CONFIGS = "dense,event,adaptive"


def cfg_bytes(c):
    flags = (c["sparse"] & 1) | (c["delta"] & 1) << 1 | (c["exit_en"] & 1) << 2 \
        | (c["recall"] & 1) << 3 | (c["adapt"] & 1) << 4
    return bytes([0xC0, flags]) + struct.pack("<H", c["cap"] & 0xFFFF) \
        + struct.pack("<i", c["exit_th"]) + bytes([c["conf_th"] & 3])


# --------------------------------------------------------------------- devices
class Fpga:
    """spark_board_top over a serial port."""

    def __init__(self, port, baud, timeout=1.0):
        import serial  # pyserial
        self.s = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.1)
        self.s.reset_input_buffer()
        self.real = True

    def _read(self, n):
        b = self.s.read(n)
        if len(b) != n:
            raise IOError(f"timeout: expected {n} bytes, got {len(b)}")
        return b

    def ping(self):
        self.s.write(b"\xE0")
        return self._read(1) == b"\x5A"

    def set_config(self, c):
        self.s.write(cfg_bytes(c))
        r = self._read(1)
        if r != b"\xC1":
            raise IOError(f"bad config ack {r!r}")

    def marker(self, on):
        self.s.write(b"\xA1" if on else b"\xA0")
        self._read(1)

    def token(self, b):
        self.s.write(bytes([0xD0, b]))
        r = self._read(7)
        chk = 0
        for x in r[:6]:
            chk ^= x
        if chk != r[6] or r[1] > 2:
            raise IOError(f"corrupt reply {r.hex()}")
        return r[0], r[1], struct.unpack("<I", r[2:6])[0]

    def close(self):
        self.s.close()


class DryRun:
    """Golden model in place of the board (no cycle counts: tok_cycles = None)."""

    def __init__(self):
        import spark_golden as sg
        self.sg = sg
        self.g = sg.Golden(sg.Weights(), sg.Cfg())
        self.real = False

    def ping(self):
        return True

    def set_config(self, c):
        self.g.c = self.sg.Cfg(**c)

    def marker(self, on):
        pass

    def token(self, b):
        o = self.g.step(b)
        return o["pred"], o["path"], None

    def close(self):
        pass


class GoldenCheck:
    """Mirror of the board state in the golden model, for per-token checking."""

    def __init__(self):
        import spark_golden as sg
        self.sg = sg
        self.g = sg.Golden(sg.Weights(), sg.Cfg())

    def set_config(self, c):
        self.g.c = self.sg.Cfg(**c)

    def step(self, b):
        o = self.g.step(b)
        return o["pred"], o["path"]


# --------------------------------------------------------------------- power
class PowerLog(threading.Thread):
    """Reads the ESP32 CSV stream; stores (host_monotonic_s, power_mW)."""

    def __init__(self, port, baud):
        super().__init__(daemon=True)
        import serial
        self.s = serial.Serial(port, baud, timeout=0.5)
        self.samples = []          # (t_host, power_mW, bus_V, current_mA)
        self.lock = threading.Lock()
        self.stop_ev = threading.Event()
        self.simulated = False
        self.cols = None
        self.s.write(b"S\n")      # (re)start streaming; the logger re-sends its header

    def run(self):
        buf = b""
        while not self.stop_ev.is_set():
            buf += self.s.read(4096)
            *lines, buf = buf.split(b"\n")
            now = time.monotonic()
            for ln in lines:
                ln = ln.decode(errors="replace").strip()
                if not ln or ln.startswith("#"):
                    continue
                f = ln.split(",")
                if f[0] == "t_ms":
                    self.cols = {k: i for i, k in enumerate(f)}
                    continue
                if not self.cols:
                    if len(f) != len(ESP_COLS):
                        continue
                    self.cols = {k: i for i, k in enumerate(ESP_COLS)}   # header missed
                try:
                    p = float(f[self.cols["power_mW"]])
                    v = float(f[self.cols["bus_V"]])
                    i = float(f[self.cols["current_mA"]])
                except (ValueError, IndexError, KeyError):
                    continue
                with self.lock:
                    self.samples.append((now, p, v, i))

    def mark(self, on):
        self.s.write(b"M1\n" if on else b"M0\n")

    def window(self, t0, t1):
        with self.lock:
            return [s[1] for s in self.samples if t0 <= s[0] <= t1]

    def stop(self):
        self.stop_ev.set()


class SimPower:
    """SIMULATED power source for --dry-run (tests the arithmetic only).

    Idle windows return ~550 mW; a run window returns idle + `extra` mW, where
    `extra` is set by the caller just before the run window is read."""

    def __init__(self):
        self.simulated = True
        self.extra = 0.0

    def start(self):
        pass

    def mark(self, on):
        pass

    def window(self, t0, t1, n=200):
        out = [550.0 + 2.0 * math.sin(k) + self.extra for k in range(n)]
        self.extra = 0.0
        return out

    def stop(self):
        pass


# --------------------------------------------------------------------- bench
def mean_std(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None
    return statistics.mean(xs), (statistics.stdev(xs) if len(xs) > 1 else 0.0)


def fmt(m, s, nd=2):
    if m is None:
        return "n/a"
    return f"{m:.{nd}f} ± {s:.{nd}f}"


def run(args):
    if args.dry_run:
        dev = DryRun()
    else:
        dev = Fpga(args.port, args.baud)
    power = None
    if args.power_port:
        power = PowerLog(args.power_port, args.power_baud)
        power.start()
        time.sleep(1.0)
        if not power.samples:
            print("warning: no samples from the power logger yet", file=sys.stderr)
    elif args.dry_run and not args.no_sim_power:
        power = SimPower()
    check = GoldenCheck() if (not args.no_check and not args.dry_run) else None

    if args.text:
        data = open(args.text, "rb").read()
    else:
        import spark_golden as sg
        data = sg.stim_text()
    if args.max_tokens:
        data = data[:args.max_tokens]
    if not dev.ping():
        raise SystemExit("no ping reply (0x5A) from the board")
    print(f"ping ok; {len(data)} tokens per run; device={'golden (dry-run)' if args.dry_run else args.port}")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = args.out or os.path.join(HERE, "..", "results", f"board_{stamp}")
    os.makedirs(out, exist_ok=True)
    runs, tokrows = [], []
    names = [n.strip() for n in args.configs.split(",") if n.strip()]
    for n in names:
        if n not in CONFIGS:
            raise SystemExit(f"unknown config {n}; choose from {', '.join(CONFIGS)}")

    for name in names:
        c = CONFIGS[name]
        for rep in range(args.repeats):
            if c is not None:
                dev.set_config(c)
                if check:
                    check.set_config(c)
            # warm-up (not timed); also advances golden mirror
            for b in data[:args.warmup_tokens]:
                if c is None:
                    dev.ping()
                else:
                    dev.token(b)
                    if check:
                        check.step(b)
            # idle baseline
            p_idle = None
            if power:
                t0 = time.monotonic()
                time.sleep(args.idle_s)
                w = power.window(t0, time.monotonic())
                p_idle = statistics.mean(w) if w else None
            # timed run
            dev.marker(True)
            if power:
                power.mark(True)
            mism = 0
            paths = [0, 0, 0]
            cycles = []
            t_run0 = time.monotonic()
            ntok = 0
            passes = 0
            while True:      # whole passes over the text until --min-run-s is reached
                for b in data:
                    tt = time.perf_counter()
                    if c is None:
                        dev.ping()
                        pred, path, cyc = None, None, None
                    else:
                        pred, path, cyc = dev.token(b)
                        paths[path] += 1
                        if cyc is not None:
                            cycles.append(cyc)
                        if check:
                            gp = check.step(b)
                            if gp != (pred, path):
                                mism += 1
                    dt = time.perf_counter() - tt
                    tokrows.append(dict(config=name, repeat=rep, i=ntok, byte=b, pred=pred, path=path,
                                        tok_cycles=cyc, wall_us=round(dt * 1e6, 1)))
                    ntok += 1
                passes += 1
                if args.dry_run or time.monotonic() - t_run0 >= args.min_run_s:
                    break
            t_run1 = time.monotonic()
            if isinstance(power, SimPower):
                # pretend a run costs extra power; purely to exercise the arithmetic
                power.extra = {"dense": 40.0, "uart-control": 3.0}.get(name, 12.0)
            dev.marker(False)
            if power:
                power.mark(False)
            dur = t_run1 - t_run0
            p_run = None
            if power:
                w = power.window(t_run0, t_run1)
                p_run = statistics.mean(w) if w else None
            e_tot = p_run * dur / ntok if p_run is not None else None            # mJ
            e_abv = (p_run - p_idle) * dur / ntok if (p_run is not None and p_idle is not None) else None
            cyc_mean = statistics.mean(cycles) if cycles else None
            row = dict(config=name, repeat=rep, tokens=ntok, passes=passes, wall_s=round(dur, 4),
                       tokens_per_s=round(ntok / dur, 2),
                       cycles_per_token=cyc_mean,
                       core_time_us_per_token=(cyc_mean / CLK_HZ * 1e6) if cyc_mean else None,
                       path_full=paths[0], path_exit=paths[1], path_recall=paths[2],
                       golden_mismatches=(mism if (check and c is not None) else None),
                       p_idle_mW=p_idle, p_run_mW=p_run,
                       e_total_uJ_per_token=(e_tot * 1e3 if e_tot is not None else None),
                       e_above_idle_uJ_per_token=(e_abv * 1e3 if e_abv is not None else None),
                       power_source=("SIMULATED" if power and power.simulated else
                                     ("INA219" if power else "none")),
                       ambient_C=args.ambient_c, cfg=(None if c is None else c))
            runs.append(row)
            print(f"{name:14s} rep {rep}: {ntok} tok in {dur:.3f}s"
                  + (f", {cyc_mean:.0f} cyc/tok" if cyc_mean else "")
                  + (f", mismatches {mism}" if (check and c is not None) else "")
                  + (f", P_idle {p_idle:.1f} mW, P_run {p_run:.1f} mW" if p_run is not None and p_idle is not None else ""))

    if power:
        power.stop()
    dev.close()

    with open(os.path.join(out, "runs.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(runs[0].keys()))
        w.writeheader()
        w.writerows(runs)
    with open(os.path.join(out, "tokens.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tokrows[0].keys()))
        w.writeheader()
        w.writerows(tokrows)

    src = runs[0]["power_source"]
    with open(os.path.join(out, "summary.md"), "w") as f:
        f.write("# SPARK board benchmark\n\n")
        f.write(f"- device: {'golden model (DRY RUN, no hardware)' if args.dry_run else args.port}\n")
        f.write(f"- power source: {src}" + (" -- numbers below are NOT measurements" if src == "SIMULATED" else "") + "\n")
        f.write(f"- text length: {len(data)} bytes (runs repeat it for >= {args.min_run_s} s), warm-up tokens: {args.warmup_tokens}, repeats: {args.repeats}, idle window: {args.idle_s} s\n")
        f.write(f"- ambient temperature: {args.ambient_c if args.ambient_c is not None else 'not recorded'} °C\n")
        f.write("- E_total = whole-board energy (incl. BL616 USB bridge, regulators, LEDs); "
                "E_above = above the idle baseline. Both include UART/USB traffic; compare with uart-control.\n\n")
        f.write("| Config | Cycles/token | Core time/token (µs @27 MHz) | Tokens/s (wall) | P_idle (mW) | P_run (mW) "
                "| E_total/token (µJ) | E_above-idle/token (µJ) | Paths full/exit/recall | Golden mismatches |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for name in names:
            rs = [r for r in runs if r["config"] == name]
            g = lambda k: mean_std([r[k] for r in rs])
            mm = [r["golden_mismatches"] for r in rs if r["golden_mismatches"] is not None]
            f.write(f"| {name} | {fmt(*g('cycles_per_token'), 1)} | {fmt(*g('core_time_us_per_token'), 2)} "
                    f"| {fmt(*g('tokens_per_s'), 1)} | {fmt(*g('p_idle_mW'), 1)} | {fmt(*g('p_run_mW'), 1)} "
                    f"| {fmt(*g('e_total_uJ_per_token'), 1)} | {fmt(*g('e_above_idle_uJ_per_token'), 2)} "
                    f"| {rs[-1]['path_full']}/{rs[-1]['path_exit']}/{rs[-1]['path_recall']} "
                    f"| {sum(mm) if mm else 'n/a'} |\n")
        f.write("\nValues are mean ± sample std over repeats. Cycles are counted in the core "
                "(tok_cycles); n/a in dry-run (the golden model does not count cycles) and for uart-control.\n")
    print("wrote", os.path.abspath(out))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", help="FPGA UART (BL616), e.g. /dev/ttyUSB1 or COM5")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--power-port", help="ESP32 INA219 logger serial port")
    ap.add_argument("--power-baud", type=int, default=921600)
    ap.add_argument("--text", help="file to stream byte-by-byte (default: golden stim text)")
    ap.add_argument("--max-tokens", type=int, default=0)
    ap.add_argument("--configs", default=DEFAULT_CONFIGS,
                    help=f"comma list from: {', '.join(CONFIGS)}")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmup-tokens", type=int, default=32)
    ap.add_argument("--idle-s", type=float, default=10.0)
    ap.add_argument("--min-run-s", type=float, default=10.0,
                    help="repeat the text (whole passes) until a run lasts at least this long, "
                         "so the power logger collects enough samples (ignored in --dry-run)")
    ap.add_argument("--ambient-c", type=float, default=None, help="ambient temperature to record")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--dry-run", action="store_true", help="use the golden model instead of hardware")
    ap.add_argument("--no-sim-power", action="store_true", help="dry-run without simulated power")
    ap.add_argument("--no-check", action="store_true", help="skip the per-token golden comparison")
    args = ap.parse_args()
    if not args.dry_run and not args.port:
        ap.error("--port is required unless --dry-run")
    run(args)


if __name__ == "__main__":
    main()
