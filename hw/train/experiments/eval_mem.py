"""20,000-byte cal/test accuracy: network alone, today's chip (one 3-byte recall, effort 2), memory priming."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/..')
sys.path.insert(0, HERE + '/../../golden')
import spark_golden as sg, train_spark_v0 as tr, spark_memory as sm, fastsim
from recall_lib import recall
data = tr.load_corpus(3_000_000); n = len(data); NB = 20000
streams = {sp: data[st: st + NB].astype(np.int64) for sp, st in [('cal', int(n * .9)), ('test', int(n * .95))]}
mem = {sp: sm.hits(s) for sp, s in streams.items()}
r3 = {sp: recall(s, (3,), 10) for sp, s in streams.items()}
for run in sys.argv[1:]:
    W = sg.Weights.from_npz(os.path.join(run, 'spark_v0_model.npz'))
    out = []
    for sp, seq in streams.items():
        _, _, _, LM = fastsim.run(W, seq); y = seq[1:]; LM = LM[:-1]; H = mem[sp][:-1]
        srt = np.sort(LM, 1); marg = srt[:, -1] - srt[:, -2]; netp = LM.argmax(1)
        p3 = r3[sp][0]; chip = np.where((p3 >= 0) & (marg < 64), p3, netp)
        pr = sm.boost_logits(LM, H).argmax(1)
        out.append(f'{sp}: net {np.mean(netp == y):.1%} chip-today {np.mean(chip == y):.1%} priming {np.mean(pr == y):.1%}')
    print(f'{os.path.basename(run):22s}', ' | '.join(out), flush=True)
