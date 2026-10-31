#!/usr/bin/env python3
"""Turns measure.py results into a plain report: speed, energy and electricity cost per million tokens, and what batching changes.
usage: python report.py RESULTS.json [MORE.json ...] [--kwh-price 8.0] [--currency INR] [--out report.md]
Electricity cost uses only your own kWh price. Energy is board power from nvidia-smi (not wall power); label: MEASURED on this machine, one run, one decode library."""
import json, sys
a = sys.argv[1:]
def opt(k, d):
    return a[a.index(k) + 1] if k in a else d
price = float(opt("--kwh-price", 0)); cur = opt("--currency", ""); out = opt("--out", "report.md")
files = [x for i, x in enumerate(a) if x.endswith(".json")]
L = ["# Your decode speed, energy and cost (MEASURED on this machine; one run per point)", ""]
for f in files:
    r = json.load(open(f)); runs = [x for x in r["runs"] if "error" not in x]
    L += [f"## {r['model']} on {r['gpu']}", "", f"Copy bandwidth {r['bandwidth_copy_gbs']:.0f} GB/s, idle board power {r['idle_power_w'] if r['idle_power_w'] is not None else 'N/A'} W, weights {r['weight_bytes']/1e9:.2f} GB, prompt {r['prompt']} tokens, {r['new']} new tokens.", "",
          "| batch | tokens/s per user | tokens/s total | board power W | joules per token | " + (f"{cur} electricity per million tokens |" if price else "kWh per million tokens |"), "|---|---|---|---|---|---|"]
    for x in runs:
        j = x.get("joules_per_token_gross"); kwh = j * 1e6 / 3.6e6 if j is not None else None
        c = f"{kwh * price:.2f}" if (kwh is not None and price) else (f"{kwh:.3f}" if kwh is not None else "N/A")
        L.append(f"| {x['batch']} | {x['tokens_per_s_per_user']:.1f} | {x['tokens_per_s_total']:.1f} | {x['mean_power_w'] if x['mean_power_w'] is not None else 'N/A'} | {f'{j:.3f}' if j is not None else 'N/A'} | {c} |")
    for x in r["runs"]:
        if "error" in x: L.append(f"| {x['batch']} | out of memory | | | | |")
    L.append("")
    js = [(x["batch"], x["joules_per_token_gross"]) for x in runs if x.get("joules_per_token_gross") is not None]
    if len(js) >= 2:
        b0, j0 = js[0]; b1, j1 = min(js, key=lambda t: t[1])
        L += [f"- Best batch for energy: **{b1}** ({j1:.3f} J per token), {j0/j1:.1f}x less energy per token than batch {b0}." if b1 != b0 else f"- Energy per token is lowest at batch {b0}."]
    sp = [(x["batch"], x["tokens_per_s_per_user"]) for x in runs]
    if len(sp) >= 2: L.append(f"- Each user's speed goes from {sp[0][1]:.1f} tokens/s at batch {sp[0][0]} to {sp[-1][1]:.1f} at batch {sp[-1][0]}; total throughput goes from {runs[0]['tokens_per_s_total']:.1f} to {runs[-1]['tokens_per_s_total']:.1f}.")
    kvb = runs[0]["tokens_per_s_per_user"] * r["weight_bytes"] / 1e9 if runs else 0
    L.append(f"- At batch 1 this run streamed about {kvb:.0f} GB/s of weights, {100*kvb/r['bandwidth_copy_gbs']:.0f}% of the measured copy bandwidth (the rest is software overhead, cache and compute).")
    L.append("")
L += ["Notes: board power as reported by nvidia-smi, not wall power; the first token after a prompt is included in the time; results depend on the software version and power mode. If any power column says N/A, your GPU does not report power."]
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
