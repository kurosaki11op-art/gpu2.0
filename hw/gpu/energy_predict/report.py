#!/usr/bin/env python3
"""One-page plain-language report from measure.py results.
usage: python report.py RESULT1.json [RESULT2.json ...] [--kwh-price 8.0] [--gpu-hour-price 25.0] [--currency INR] [--out report]
Writes report.md and report.html (open the html in a browser; it prints to one page).
--kwh-price: your electricity price per kWh (energy cost per million tokens). --gpu-hour-price: what an hour of this GPU costs you (rent, or your own estimate); gives the cost per million tokens from speed alone.
Label: MEASURED on this machine, one run per point, board power from nvidia-smi (not wall power), one decode library in its default setup."""
import html, json, sys
a = sys.argv[1:]
def opt(k, d):
    return a[a.index(k) + 1] if k in a else d
kwh = float(opt("--kwh-price", 0)); gph = float(opt("--gpu-hour-price", 0)); cur = opt("--currency", ""); out = opt("--out", "report")
files = [x for x in a if x.endswith(".json")]
md = ["# What your GPU really does with AI models", "", "Measured on this machine. One run per point; board power from nvidia-smi (not wall power); the library's default decode setup (no CUDA graphs).", ""]
for f in files:
    r = json.load(open(f)); runs = [x for x in r["runs"] if "error" not in x]
    if not runs: md += [f"## {r['model']}: no successful run ({[x.get('error') for x in r['runs']]})", ""]; continue
    floor_ms = r["weight_bytes"] / (r["bandwidth_copy_gbs"] * 1e9) * 1e3; b1 = runs[0]; ms1 = 1e3 * b1["seconds"] / b1["new_tokens"]; frac = floor_ms / ms1
    md += [f"## {r['model']} on {r['gpu']}", "", f"- Model weights {r['weight_bytes']/1e9:.2f} GB; your GPU's memory speed {r['bandwidth_copy_gbs']:.0f} GB/s; idle power {r['idle_power_w']:.1f} W." if r.get("idle_power_w") is not None else f"- Model weights {r['weight_bytes']/1e9:.2f} GB; memory speed {r['bandwidth_copy_gbs']:.0f} GB/s.", ""]
    head = "| users at once (batch) | speed per user (tokens/s) | total speed (tokens/s) | power (W) | energy per token (J) |" + (f" electricity per million tokens ({cur}) |" if kwh else "") + (f" GPU cost per million tokens ({cur}) |" if gph else "")
    md += [head, "|---|---|---|---|---|" + ("---|" if kwh else "") + ("---|" if gph else "")]
    for x in runs:
        j = x.get("joules_per_token_gross"); row = f"| {x['batch']} | {x['tokens_per_s_per_user']:.1f} | {x['tokens_per_s_total']:.1f} | {f"{x['mean_power_w']:.1f}" if x['mean_power_w'] is not None else 'n/a'} | {f'{j:.3f}' if j is not None else 'n/a'} |"
        if kwh: row += f" {j * 1e6 / 3.6e6 * kwh:.2f} |" if j is not None else " n/a |"
        if gph: row += f" {gph / (x['tokens_per_s_total'] * 3600) * 1e6:.2f} |"
        md.append(row)
    md.append("")
    js = [(x["batch"], x["joules_per_token_gross"]) for x in runs if x.get("joules_per_token_gross") is not None]
    md.append("**What this means for you**"); md.append("")
    if len(js) >= 2:
        b0, j0 = js[0]; bb, jb = min(js, key=lambda t: t[1]); sp0 = runs[0]["tokens_per_s_per_user"]; spb = [x for x in runs if x["batch"] == bb][0]["tokens_per_s_per_user"]
        if bb != b0: md.append(f"- **Serve several users at once.** At batch {bb} each token costs {j0/jb:.1f}x less energy than at batch {b0} ({jb:.3f} J against {j0:.3f} J). Each user gets {spb:.0f} tokens/s instead of {sp0:.0f}.")
    if gph:
        c = [(x["batch"], gph / (x["tokens_per_s_total"] * 3600) * 1e6) for x in runs]; c0, cb = c[0], min(c, key=lambda t: t[1])
        if cb[0] != c0[0]: md.append(f"- **Cost per million tokens falls from {c0[1]:.2f} to {cb[1]:.2f} {cur}** at batch {cb[0]} (at {gph:g} {cur} per GPU hour).")
    md.append(f"- **How close to the memory limit you run:** at batch 1 this setup reaches {100*frac:.0f}% of the speed the GPU's memory allows for this model.")
    if frac < 0.5: md.append(f"- **There may be a large gain from the software setup.** In our own test on a different GPU (a Colab T4), turning on CUDA graphs in a serving engine made batch-1 decode 2.5x to 4.7x faster and reached 72% to 95% of the memory limit. **This is not measured on your machine**; treat it as something to try, not a promise.")
    else: md.append("- Your setup is already close to the memory limit at batch 1; the remaining gain is from batching.")
    md.append("")
md += ["---", "Notes: energy is board power from nvidia-smi, not wall power; results depend on drivers, library versions and power mode; one run per point; small models only. Tool and method: hw/gpu/energy_predict in the project repository."]
open(out + ".md", "w", encoding="utf-8").write("\n".join(md) + "\n")
body = []; intable = False
for line in md:
    if intable and not line.startswith('|'): body.append('</table>'); intable = False
    if line.startswith("# "): body.append(f"<h1>{html.escape(line[2:])}</h1>")
    elif line.startswith("## "): body.append(f"<h2>{html.escape(line[3:])}</h2>")
    elif line.startswith("- "): body.append("<p class='b'>" + html.escape(line[2:]).replace("**", "<b>", 1).replace("**", "</b>", 1) + "</p>")
    elif line.startswith("|") and set(line.replace("|", "").strip()) <= set("- "): continue
    elif line.startswith("|"):
        cells = [c.strip() for c in line.strip("|").split("|")]; head = "users at once" in line
        if head: body.append(("</table>" if intable else "") + "<table>"); intable = True
        tag = "th" if head else "td"; body.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
    elif line.startswith("**"): body.append(f"<p><b>{html.escape(line.strip('*'))}</b></p>")
    elif line == "---": body.append("<hr>")
    elif line: body.append(f"<p>{html.escape(line)}</p>")
if intable: body.append("</table>")
doc = "<!doctype html><meta charset='utf-8'><title>GPU report</title><style>body{font:15px/1.5 system-ui,sans-serif;max-width:900px;margin:24px auto;padding:0 16px}table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #bbb;padding:4px 8px;text-align:right}th{background:#eee}.b{margin:4px 0 4px 16px}@media print{body{margin:8mm}}</style>" + "\n".join(body)
open(out + ".html", "w", encoding="utf-8").write(doc)
print("\n".join(md)); print("\nwritten", out + ".md", "and", out + ".html")
