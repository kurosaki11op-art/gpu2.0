import sys, numpy as np
from recall_lib import recall
for feats in sys.argv[1:]:
    F = np.load(feats)
    for split in ('cal', 'test'):
        seq, LM = F[split + '_seq'].astype(np.int64), F[split + '_lm'].astype(np.int64)
        N = len(seq) - 1; y = seq[1:]; LM = LM[:N]
        srt = np.sort(LM, 1); margin = srt[:, -1] - srt[:, -2]; netp = LM.argmax(1)
        p3, c3, _ = recall(seq, (3,), 10); hit = p3 >= 0
        cur = np.mean(np.where(hit & (margin < 64), p3, netp) == y)       # chip today, effort 2, arb_th 64
        cur0 = np.mean(np.where(hit, p3, netp) == y)
        lg = LM.copy()
        for k in (2, 3, 4, 6):
            p, c, _ = recall(seq, (k,), 10); h = np.where(p >= 0)[0]
            lg[h, p[h]] += ((64 + 32 * c[h]) * k) // 3
        pr = np.mean(lg.argmax(1) == y)
        print(f'{feats} {split}: network {np.mean(netp == y):.1%} | chip today effort1 {cur0:.1%} effort2 {cur:.1%} | priming 4 memories {pr:.1%}  (first 2000: {np.mean(lg.argmax(1)[:2000] == y[:2000]):.1%})', flush=True)
