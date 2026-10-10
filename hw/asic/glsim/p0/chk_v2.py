import sys, numpy as np
sys.path.insert(0, '/home/user/gpu2.0/hw/golden'); import spark_golden as sg
args = dict(a.split('=') for a in sys.argv[1].replace('+', '').split())
m = {'sparse': 'sparse', 'delta': 'delta', 'adapt': 'adapt', 'exit': 'exit_en', 'exit_th': 'exit_th',
     'recall': 'recall', 'conf_th': 'conf_th', 'cap': 'cap', 'rmode': 'recall_mode', 'arb_th': 'arb_th', 'thr': None}
w = sg.Weights.from_npz(sys.argv[2]) if len(sys.argv) > 2 else sg.Weights()
w.pad_ctx(3)
stim = np.load('stim.npy') if len(sys.argv) > 2 else sg.stim_text()
g = sg.Golden(w, sg.Cfg(**{m[k]: int(v) for k, v in args.items() if m.get(k)}))
rtl = [list(map(int, l.split())) for l in open('rtl_out.txt')]
bad = 0
for i, (b, r) in enumerate(zip(stim, rtl)):
    o = g.step(int(b)); exp = [o['pred'], o['path']] + o['ev'] + o['proc']
    if exp != r[:10]:
        bad += 1
        if bad <= 3: print('  token', i, 'golden', exp, 'rtl', r[:10])
acc = np.mean([r[0] == stim[i + 1] for i, r in enumerate(rtl[:-1])])
print(sys.argv[1], 'tokens', len(rtl), 'mismatches', bad, 'cycles/token', round(sum(r[10] for r in rtl) / len(rtl)), f'acc {acc:.1%}')
