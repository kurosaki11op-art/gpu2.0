"""Train a small SPARK-v0-compatible spiking byte model and export int4 weights.

The forward pass reproduces the chip's integer rules exactly (floor shifts,
saturation, spike clamp, reset by subtraction) with straight-through estimators,
so the exported integers run bit-exact on hw/golden/spark_golden.py and the RTL.

Data: Python source files from the local Python standard library (real code,
same domain as L's training data).

Usage: python3 hw/train/train_spark_v0.py --out hw/train/out
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as sg  # noqa: E402

D, H, V = sg.D, sg.H, sg.V


def load_corpus(max_bytes):
    files = sorted(glob.glob("/usr/lib/python3*/**/*.py", recursive=True))
    rng = np.random.default_rng(0)
    rng.shuffle(files)
    buf, n = [], 0
    for f in files:
        try:
            b = open(f, "rb").read()
        except OSError:
            continue
        if b"\0" in b:
            continue
        buf.append(b)
        n += len(b)
        if n >= max_bytes:
            break
    data = b"".join(buf)[:max_bytes]
    return np.frombuffer(data, dtype=np.uint8).copy()


RELAX = [False]   # True: no rounding/floors (same value ranges) for pre-training


def ste_round(x):
    if RELAX[0]:
        return x
    return x + (torch.round(x) - x).detach()


def ste_floor(x):
    if RELAX[0]:
        return x
    return x + (torch.floor(x) - x).detach()


def q4(w):
    """int4 weights with straight-through gradient."""
    return torch.clamp(ste_round(w), -8, 7)


class SparkV0(torch.nn.Module):
    def __init__(self, a=230, acc_sh=2, s_sh=4, ctx=1, spike_mode="sym", shared_emb=False):
        super().__init__()
        self.a, self.acc_sh, self.s_sh, self.ctx = a, acc_sh, s_sh, ctx
        self.spike_mode = spike_mode     # "sym": sign(h)*min(|h|>>s,7)  "thr": min((h-th)>>s,7), >=0
        g = torch.Generator().manual_seed(0)
        init = lambda *s, sc: torch.nn.Parameter(torch.randn(*s, generator=g) * sc)
        self.emb = init(V, D, sc=3.0)
        # extra embedding tables for the previous ctx-1 bytes (context window)
        self.shared_emb = shared_emb      # one table for all context positions (saves chip memory)
        self.embx = torch.nn.ParameterList(
            [] if shared_emb else [init(V, D, sc=3.0) for _ in range(ctx - 1)])
        self.w0 = init(H, D * ctx, sc=1.5)
        self.w1 = init(H, H, sc=1.5)
        self.we = init(V, H, sc=1.5)
        self.wm = init(V, H, sc=1.5)
        # per-neuron firing thresholds (integer, used when spike_mode == "thr")
        self.th0 = torch.nn.Parameter(torch.zeros(H))
        self.th1 = torch.nn.Parameter(torch.zeros(H))

    def spike(self, h, th=None):
        """Exact clamp/floor spike with a surrogate gradient."""
        step = 2.0 ** self.s_sh
        if self.spike_mode == "thr":
            u = h - ste_round(th)
            if RELAX[0]:
                return torch.clamp(u / step, 0.0, 7.0)
            s_exact = torch.clamp(torch.floor(u / step), 0, 7)
            s_soft = torch.clamp(u / step, -0.5, 7.5)
            return s_soft + (s_exact - s_soft).detach()
        if RELAX[0]:
            return torch.clamp(h / step, -7.0, 7.0)
        mag_exact = torch.clamp(torch.floor(torch.abs(h) / step), max=7)
        s_exact = torch.sign(h) * mag_exact
        # surrogate: slope 1/step inside the active range, 0 outside
        s_soft = torch.clamp(h / step, -7.5, 7.5)
        return s_soft + (s_exact - s_soft).detach()

    def layer(self, h, x, w, th=None):
        acc = x @ q4(w).t()
        dec = ste_floor(h * self.a / 256.0)
        hv = dec + ste_floor(acc / 2.0 ** self.acc_sh)
        hv = hv + (torch.clamp(hv, -32768, 32767) - hv).detach()
        s = self.spike(hv, th)
        return hv - s * 2.0 ** self.s_sh, s

    def forward(self, seq, h0=None, h1=None):
        """seq: [B, T] bytes. Returns main logits, exit logits, spikes stats, states."""
        B, T = seq.shape
        if h0 is None:
            h0 = torch.zeros(B, H, dtype=self.emb.dtype)
            h1 = torch.zeros(B, H, dtype=self.emb.dtype)
        if self.shared_emb:
            embs = [q4(self.emb)] * self.ctx
        else:
            embs = [q4(self.emb)] + [q4(e) for e in self.embx]
        outs_m, outs_e, rates = [], [], []
        for t in range(T):
            parts = []
            for k, e in enumerate(embs):
                if t - k >= 0:
                    parts.append(e[seq[:, t - k]])
                else:
                    parts.append(torch.zeros(B, D, dtype=e.dtype))
            x = torch.cat(parts, 1)
            h0, s0 = self.layer(h0, x, self.w0, self.th0)
            h1, s1 = self.layer(h1, s0, self.w1, self.th1)
            outs_e.append(s0 @ q4(self.we).t())
            outs_m.append(s1 @ q4(self.wm).t())
            rates.append(torch.cat([s0.abs(), s1.abs()], 1))
        return torch.stack(outs_m, 1), torch.stack(outs_e, 1), torch.stack(rates, 1), h0, h1

    def export(self):
        with torch.no_grad():
            out = {k: q4(getattr(self, n)).round().to(torch.int64).numpy().astype(np.int8)
                   for k, n in [("emb", "emb"), ("w0", "w0"), ("w1", "w1"),
                                ("w_exit", "we"), ("w_main", "wm")]}
            out["th0"] = ste_round(self.th0).round().to(torch.int64).numpy().astype(np.int16)
            out["th1"] = ste_round(self.th1).round().to(torch.int64).numpy().astype(np.int16)
            out["ctx"] = np.array([self.ctx], dtype=np.int16)
            out["shared_emb"] = np.array([1 if self.shared_emb else 0], dtype=np.int16)
            for i, e in enumerate(self.embx):
                out[f"emb{i + 1}"] = q4(e).round().to(torch.int64).numpy().astype(np.int8)
            return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--bytes", type=int, default=3_000_000)
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--seq", type=int, default=64)
    ap.add_argument("--lr", type=float, default=0.02)
    ap.add_argument("--sparsity", type=float, default=0.02)
    ap.add_argument("--target-rate", type=float, default=0.08)
    ap.add_argument("--eval-bytes", type=int, default=3000)
    ap.add_argument("--ctx", type=int, default=1, help="bytes of context window (1 = SPARK v0)")
    ap.add_argument("--shared-emb", action="store_true", help="one embedding table for all context bytes")
    ap.add_argument("--hidden", type=int, default=0, help="neurons per layer (default: chip size 128)")
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--warmup", type=int, default=100)
    ap.add_argument("--relax-steps", type=int, default=0,
                    help="first N steps without rounding (then exact integer QAT)")
    ap.add_argument("--acc-sh", type=int, default=2)
    ap.add_argument("--spike", default="sym", choices=["sym", "thr"])
    ap.add_argument("--s-sh", type=int, default=4)
    ap.add_argument("--decay", type=int, default=230)
    ap.add_argument("--relax-only", action="store_true",
                    help="evaluate the relaxed (non-integer) model: architecture ceiling only")
    a = ap.parse_args()
    if a.hidden:
        global H
        H = a.hidden          # size study only: the v0 chip and golden model use 128
    os.makedirs(a.out, exist_ok=True)
    torch.manual_seed(0)
    torch.set_num_threads(a.threads or os.cpu_count() or 4)

    data = load_corpus(a.bytes)
    n = len(data)
    train, cal, test = data[: int(n * 0.9)], data[int(n * 0.9): int(n * 0.95)], data[int(n * 0.95):]
    print(f"corpus {n} bytes; train {len(train)} cal {len(cal)} test {len(test)}")

    model = SparkV0(a=a.decay, acc_sh=a.acc_sh, s_sh=a.s_sh, ctx=a.ctx, spike_mode=a.spike,
                    shared_emb=a.shared_emb)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda st: min(1.0, (st + 1) / a.warmup) * 0.5 * (1 + np.cos(np.pi * min(st, a.steps) / a.steps)))
    rng = np.random.default_rng(1)
    t0 = time.time()
    temp = 1.0 / 32.0          # logits are large integers; scale for the loss only
    for step in range(a.steps):
        RELAX[0] = a.relax_only or step < a.relax_steps
        idx = rng.integers(0, len(train) - a.seq - 2, size=a.batch)
        seq = torch.from_numpy(np.stack([train[i:i + a.seq + 1] for i in idx]).astype(np.int64))
        lm, le, rates, _, _ = model(seq[:, :-1])
        tgt = seq[:, 1:]
        warm = 8  # let the membrane state settle before scoring
        loss_m = F.cross_entropy(lm[:, warm:].reshape(-1, V) * temp, tgt[:, warm:].reshape(-1))
        loss_e = F.cross_entropy(le[:, warm:].reshape(-1, V) * temp, tgt[:, warm:].reshape(-1))
        fire = (rates > 0).float().mean()
        satur = (rates >= 6.99).float().mean()
        loss = loss_m + 0.3 * loss_e + a.sparsity * F.relu(rates.mean() - a.target_rate) * 10
        opt.zero_grad()
        loss.backward()
        opt.step()
        sched.step()
        if step % 100 == 0 or step == a.steps - 1:
            print(f"step {step:5d} loss_main {loss_m.item():.3f} loss_exit {loss_e.item():.3f} "
                  f"firing {fire.item():.3f} saturated {satur.item():.3f} {time.time() - t0:.0f}s", flush=True)

    # ---- export and evaluate the exact integer model
    RELAX[0] = a.relax_only
    wts = model.export()
    np.savez(os.path.join(a.out, "spark_v0_model.npz"), **wts)
    if a.ctx > 1 or a.spike != "sym":
        with torch.no_grad():
            m64 = model.double()
            tb = test[:a.eval_bytes]
            lm, le, rates, _, _ = m64(torch.from_numpy(tb.astype(np.int64))[None, :])
            pm, pe = lm[0].argmax(-1).numpy(), le[0].argmax(-1).numpy()
            srt = np.sort(le[0].numpy(), axis=1)
            res = {"ctx": a.ctx, "steps": a.steps, "spike": a.spike,
                   "next_byte_accuracy_main": float(np.mean(pm[:-1] == tb[1:])),
                   "next_byte_accuracy_exit_head": float(np.mean(pe[:-1] == tb[1:])),
                   "firing_rate": float((rates[0] > 0).double().mean()),
                   "eval_bytes": int(len(tb)),
                   "relaxed_eval": bool(a.relax_only),
                   "note": "context-window model; evaluated with the exact integer PyTorch model "
                           "(golden/RTL support for ctx>1 not built yet)"}
        json.dump(res, open(os.path.join(a.out, "result.json"), "w"), indent=2)
        print(json.dumps(res, indent=2))
        return
    W = sg.Weights.from_npz(os.path.join(a.out, "spark_v0_model.npz"))

    def run_golden(text, cfg):
        g = sg.Golden(W, cfg)
        preds, margins, rate0, rate1 = [], [], [], []
        for b in text:
            o = g.step(int(b))
            preds.append(o["pred"])
            rate0.append(np.count_nonzero(g.s[0]) / H)
            rate1.append(np.count_nonzero(g.s[1]) / H)
        return np.array(preds), np.mean(rate0), np.mean(rate1)

    base = sg.Cfg(a=model.a, acc_sh=model.acc_sh, s_sh=model.s_sh)
    cal_n, test_n = a.eval_bytes, a.eval_bytes
    calb, testb = cal[:cal_n], test[:test_n]

    # exact-match check: torch integer-mode vs golden on the test bytes
    with torch.no_grad():
        model64 = model.double()
        lm, le, _, _, _ = model64(torch.from_numpy(testb.astype(np.int64))[None, :])
        torch_pred = lm[0].argmax(-1).numpy()
        exit_logits = le[0].numpy()
    gold_pred, r0, r1 = run_golden(testb, base)
    mism = int(np.sum(torch_pred != gold_pred))
    acc_main = float(np.mean(gold_pred[:-1] == testb[1:]))

    # calibrate exit threshold on the calibration split
    with torch.no_grad():
        _, le_c, _, _, _ = model64(torch.from_numpy(calb.astype(np.int64))[None, :])
        lm_c, _, _, _, _ = model64(torch.from_numpy(calb.astype(np.int64))[None, :])
    le_c, lm_c = le_c[0].numpy(), lm_c[0].numpy()
    srt = np.sort(le_c, axis=1)
    margin = srt[:, -1] - srt[:, -2]
    ex_pred, main_pred = le_c.argmax(1), lm_c.argmax(1)
    truth = calb[1:]
    exit_th = int(margin.max()) + 1
    for th in sorted(set(int(x) for x in np.percentile(margin, np.arange(5, 100, 5)))):
        sel = margin[:-1] >= th
        if sel.sum() < 20:
            continue
        if np.mean(ex_pred[:-1][sel] == truth[sel]) >= np.mean(main_pred[:-1][sel] == truth[sel]):
            exit_th = th
            break

    cfg_exit = sg.Cfg(a=model.a, acc_sh=model.acc_sh, s_sh=model.s_sh, exit_en=1, exit_th=exit_th)
    g = sg.Golden(W, cfg_exit)
    paths, preds = [], []
    for b in testb:
        o = g.step(int(b))
        paths.append(o["path"])
        preds.append(o["pred"])
    preds = np.array(preds)
    exit_rate = float(np.mean(np.array(paths) == 1))
    acc_exit_mode = float(np.mean(preds[:-1] == testb[1:]))

    cfg = {"a": model.a, "acc_sh": model.acc_sh, "s_sh": model.s_sh, "exit_th": exit_th,
           "conf_th": 1, "train_data": "local CPython standard library .py files",
           "train_bytes": len(train), "steps": a.steps,
           "next_byte_accuracy_main": acc_main,
           "next_byte_accuracy_with_early_exit": acc_exit_mode,
           "early_exit_rate": exit_rate,
           "firing_rate_layer0": float(r0), "firing_rate_layer1": float(r1),
           "torch_vs_golden_mismatches": mism, "eval_bytes": int(test_n)}
    json.dump(cfg, open(os.path.join(a.out, "spark_v0_config.json"), "w"), indent=2)
    open(os.path.join(a.out, "sample_eval.txt"), "wb").write(bytes(test[:2000]))
    print(json.dumps(cfg, indent=2))


if __name__ == "__main__":
    main()
