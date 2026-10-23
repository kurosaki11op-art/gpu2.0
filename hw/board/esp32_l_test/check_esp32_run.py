"""End-to-end check of an ESP32 run. usage: python check_esp32_run.py LOGFILE [--ambient-c 24] [--note TEXT]   (LOGFILE = serial monitor text saved to a file)
Verifies LOGIC PASS, parses REP lines, and prints speed, power and energy per decision as mean +- std over repetitions.
Energy per decision (delta) = (run_mA - idle_mA) * bus_V / decisions_per_second; total energy per decision = run_mA * bus_V / rate.
A run is flagged UNRELIABLE if idle current drifts by more than 3% between repetitions or the delta is below 3 times the spread."""
import re, sys, statistics as st
args = sys.argv[1:]; log = open(args[0]).read()
amb = args[args.index("--ambient-c") + 1] if "--ambient-c" in args else "not recorded"
ok = re.search(r"LOGIC PASS", log) is not None; print("logic test:", "PASS" if ok else "FAIL or missing")
reps = [dict(re.findall(r"(\w+) ([-\d.]+)", l)) for l in log.splitlines() if l.startswith("REP")]
if not reps: sys.exit("no REP lines found (INA219 missing or run incomplete)")
f = lambda k: [float(r[k]) for r in reps]
idle, run, v, n, s, us = f("idle_mA"), f("run_mA"), f("bus_V"), f("decisions"), f("run_s"), f("us_per_decision")
rate = [a / b for a, b in zip(n, s)]
dP = [(r - i) * vv for r, i, vv in zip(run, idle, v)]                      # mW
e_delta = [d / rt * 1e3 for d, rt in zip(dP, rate)]                       # uJ per decision (mW / (1/s) = mJ; x1e3 -> uJ)
e_tot = [r * vv / rt * 1e3 for r, vv, rt in zip(run, v, rate)]
m = lambda x: (st.mean(x), st.stdev(x) if len(x) > 1 else 0.0)
print("repetitions: %d | ambient: %s C | cpu line: %s" % (len(reps), amb, re.findall(r"DONE.*", log)))
for name, x, u in (("speed", us, "us per decision"), ("idle current", idle, "mA"), ("run current", run, "mA"), ("delta power", dP, "mW"), ("energy per decision, delta", e_delta, "uJ"), ("energy per decision, total", e_tot, "uJ")):
    a, b = m(x); print("  %-28s %.3f +- %.3f %s" % (name, a, b, u))
drift = (max(idle) - min(idle)) / st.mean(idle) * 100; spread = m(dP)[1]
bad = drift > 3 or st.mean(dP) < 3 * spread
print("idle drift %.1f %% | verdict: %s" % (drift, "UNRELIABLE (repeat with warm board, steadier supply, longer phases)" if bad else "usable (MEASURED, ESP32 software baseline, not the L chip)"))
