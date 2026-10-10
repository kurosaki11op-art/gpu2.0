"""Fast exact main-path simulator (same integer rules as the golden model, full state every token)."""
import sys, numpy as np
HERE = __import__('os').path.dirname(__import__('os').path.abspath(__file__)); sys.path.insert(0, HERE + '/../../golden'); sys.path.insert(0, HERE + '/..')
import spark_golden as sg

def run(W, seq, a=230, acc_sh=2, s_sh=4):
    W0, W1, WE, WM = [w.astype(np.int64) for w in W.w]
    embs = [W.emb] + list(W.embx); ctx = len(embs)
    th0, th1 = W.th
    h0 = np.zeros(sg.H, np.int64); h1 = np.zeros(sg.H, np.int64)
    n = len(seq); S0 = np.zeros((n, sg.H), np.int8); S1 = np.zeros((n, sg.H), np.int8)
    LM = np.zeros((n, sg.V), np.int32); LE = np.zeros((n, sg.V), np.int32)
    def mem(h, acc, th):
        h = np.clip(((h * a) >> 8) + (acc >> acc_sh), -32768, 32767)
        s = np.clip((h - th) >> s_sh, 0, 7)
        return h - s * (1 << s_sh), s
    for t in range(n):
        x = np.concatenate([embs[k][seq[t - k]] if t - k >= 0 else np.zeros(sg.D, np.int64) for k in range(ctx)])
        h0, s0 = mem(h0, W0 @ x, th0)
        h1, s1 = mem(h1, W1 @ s0, th1)
        S0[t], S1[t], LE[t], LM[t] = s0, s1, WE @ s0, WM @ s1
    return S0, S1, LE, LM

if __name__ == '__main__':
    run_dir, nb, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    import train_spark_v0 as tr
    W = sg.Weights.from_npz(run_dir + '/spark_v0_model.npz')
    data = tr.load_corpus(3_000_000); n = len(data)
    res = {}
    for name, st in [('cal', int(n * .9)), ('test', int(n * .95))]:
        seq = data[st: st + nb].astype(np.int64)
        S0, S1, LE, LM = run(W, seq)
        res.update({name + '_seq': seq, name + '_s0': S0, name + '_s1': S1, name + '_le': LE, name + '_lm': LM})
        print(name, 'main acc', np.mean(LM.argmax(1)[:-1] == seq[1:]), flush=True)
    # check against golden on the first 300 test tokens
    g = sg.Golden(W, sg.Cfg(spike_mode='thr'))
    gp = [g.step(int(b))['pred'] for b in res['test_seq'][:300]]
    print('mismatch vs golden (300 tokens):', int(np.sum(np.array(gp) != res['test_lm'][:300].argmax(1))))
    np.savez_compressed(out, **res)
