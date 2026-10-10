"""Real floorplan of the SPARK core on the Tang Nano 20K FPGA (GW2AR-18), from the nextpnr place-and-route
result: every placed cell is drawn at its real tile position, coloured by the SPARK block it belongs to."""
import json, re, sys, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

PNR = sys.argv[1] if len(sys.argv) > 1 else '../pnr2/pnr2.json'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'spark_floorplan.png'
GROUPS = [  # (label, colour, name patterns) — first match wins
    ('Weights + embeddings (block RAM)', '#1D5E8C', [r'u_core\.u_w\d', r'u_core\.u_emb']),
    ('Recall unit (hippocampus memory)', '#B4531A', [r'u_core\.u_tab', r'u_core\.rec_', r'u_core\.t_w', r'u_core\.ctx', r'u_core\.dec']),
    ('Event scanner (skip silent / unchanged)', '#E0A030', [r'u_core\.sent', r'u_core\.mask', r'u_core\.src', r'u_core\.chg', r'u_core\.sp\b', r'u_core\.sp_',
                                                           r'u_core\.ev_', r'u_core\.nzc', r'u_core\.use_delta', r'u_core\.u_sn', r'u_core\.u_s\d', r'u_core\.prc', r'u_core\.vlat', r'u_core\.sel']),
    ('MAC engine + accumulators', '#6A3D9A', [r'u_core\.u_acc', r'u_core\.acc', r'u_core\.sum', r'u_core\.e\b', r'u_core\.wreads']),
    ('Neurons: leak, threshold, spike, argmax', '#2E8B57', [r'u_core\.n1', r'u_core\.n2', r'u_core\.h_', r'u_core\.s_', r'u_core\.po_', r'u_core\.mag',
                                                          r'u_core\.hs', r'u_core\.t1', r'u_core\.t2', r'u_core\.idx', r'u_core\.u_h\d', r'u_core\.u_th', r'u_core\.q\b', r'u_core\.q_']),
    ('Effort dial + controller', '#C2185B', [r'u_core\.score', r'u_core\.tok', r'u_core\.state', r'u_core\.stg', r'u_core\.m\b', r'u_core\.m_', r'u_core\.c\b',
                                            r'u_core\.c_', r'u_core\.done', r'u_core\.pred', r'u_core\.path', r'u_core\.cyc', r'u_core\.hist', r'u_core\.started', r'u_core\.byte',
                                            r'exit_th', r'delta_en', r'cap', r'recall_en', r'conf_th', r'sparse_en', r'adapt_en', r'thr_en', r'recall_mode', r'arb_th']),
    ('Host link (UART, config)', '#5A6577', [r'u_rx', r'u_tx', r'rbuf', r'cfgb', r'chk', r'por', r'hb', r'marker', r'state', r'cnt', r'rlen', r'tx_', r'rx_', r'tok_led', r'cfg_led', r'btn', r'start', r'in_byte', r'rst']),
]
OTHER = ('Other core logic', '#9AA5B1')
d = json.load(open(PNR)); cells = d['modules'][list(d['modules'])[0]]['cells']
pts = collections.defaultdict(list); counts = collections.Counter(); xs, ys = [], []
for name, c in cells.items():
    bel = c['attributes'].get('NEXTPNR_BEL', '')
    mt = re.match(r'X(\d+)Y(\d+)/', bel)
    if not mt:
        continue
    x, y = int(mt.group(1)), int(mt.group(2)); xs.append(x); ys.append(y)
    lab = OTHER
    for g in GROUPS:
        if any(re.match(p, name) for p in g[2]):
            lab = g[:2]; break
    pts[lab].append((x, y, c['type'])); counts[lab[0]] += 1
W, H = max(xs) + 1, max(ys) + 1
fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
fig.patch.set_facecolor('#F3F0E8'); ax.set_facecolor('#E8EEF3')
ax.add_patch(Rectangle((-0.5, -0.5), W, H, fill=False, ec='#0F1A2B', lw=2))
import random; random.seed(1)
for lab, p in sorted(pts.items(), key=lambda kv: -len(kv[1])):
    bx = [x + random.uniform(-0.35, 0.35) for x, y, t in p]; by = [y + random.uniform(-0.35, 0.35) for x, y, t in p]
    big = [t in ('SP', 'SDPB', 'DPB', 'DPX9B', 'SDPX9B', 'SPX9') for x, y, t in p]
    ax.scatter([b for b, g in zip(bx, big) if not g], [b for b, g in zip(by, big) if not g], s=6, c=lab[1], alpha=0.85, linewidths=0)
    for (x, y, t), g in zip(p, big):
        if g:
            ax.add_patch(Rectangle((x - 0.45, y - 0.45), 0.9, 0.9, fc=lab[1], ec='#0F1A2B', lw=0.6))
ax.set_xlim(-1, W); ax.set_ylim(H, -1); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
handles = [Patch(color=g[1], label=f'{g[0]}  ({counts[g[0]]:,} cells)') for g in GROUPS + [OTHER] if counts[g[0]]]
ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=14, labelspacing=1.1)
fig.subplots_adjust(left=0.01, right=0.55, top=0.98, bottom=0.02); plt.savefig(OUT, facecolor=fig.get_facecolor())
print(W, H, sum(counts.values())); [print(f'{v:6d} {k}') for k, v in counts.most_common()]
