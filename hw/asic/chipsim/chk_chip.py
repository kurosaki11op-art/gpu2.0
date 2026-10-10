"""Compare chip_out.txt (pred, path per token from the chip pins) with the golden model."""
import sys, numpy as np
sys.path.insert(0, '/home/user/gpu2.0/hw/golden'); import spark_golden as sg
w = sg.Weights.from_npz(sys.argv[1]); w.pad_ctx(3)
stim = np.load('stim.npy')
cfg = sg.Cfg(sparse=1, recall=1, conf_th=0, recall_mode=int(sys.argv[2]), arb_th=int(sys.argv[3]), adapt=1, exit_en=1, exit_th=2, spike_mode='thr')
g = sg.Golden(w, cfg)
rows = [list(map(int, l.split())) for l in open('chip_out.txt')]
bad = 0
for i, r in enumerate(rows):
    o = g.step(int(stim[i]))
    if [o['pred'], o['path']] != r[:2]:
        bad += 1
        if bad <= 3: print('  token', i, 'golden', o['pred'], o['path'], 'chip', r[:2])
acc = np.mean([r[0] == stim[i + 1] for i, r in enumerate(rows[:-1])])
print(f'chip vs golden: {len(rows)} tokens, {bad} mismatches, acc {acc:.1%}')
