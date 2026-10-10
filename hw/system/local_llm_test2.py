#!/usr/bin/env python3
"""SPARK beside a real big model on your PC (Ollama) -- corrected test (v2).

Fixes over v1: prompts end only at word-piece (token) boundaries; the big model writes its real multi-token
continuation; SPARK itself runs here (numpy only) and drafts its own continuation from the same point, so draft mode is
measured exactly (lossless greedy speculative decoding); GPU use is checked with `ollama ps` before energy is reported.

Needs: Python 3, numpy (pip install numpy), Ollama running with the model pulled.
Run:   python hw/system/local_llm_test2.py --model qwen3.5:9b [--m 150]
Send back the printed summary or hw/system/out/local_llm2_<model>.json
"""
import argparse, base64, copy, json, os, re, shutil, subprocess, sys, threading, time, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as g1          # noqa: E402  (numpy only)
import spark_golden_v2 as g2       # noqa: E402
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")


def pieces(b):
    """split bytes into approximate word-piece tokens"""
    return [m.group(0).encode("latin-1") for m in PRETOK.finditer(b.decode("latin-1"))]


def ollama(host, model, prompt, n_tokens, timeout=900):
    body = json.dumps({"model": model, "prompt": prompt, "raw": True, "stream": False, "think": False, "keep_alive": "60m",
                       "options": {"temperature": 0, "top_k": 1, "num_predict": n_tokens, "num_ctx": 4096, "seed": 0}}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def ollama_ps():
    try:
        return subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=20).stdout
    except Exception as e:
        return f"(ollama ps failed: {e})"


class PowerMeter:
    def __init__(self):
        self.ok = shutil.which("nvidia-smi") is not None; self.samples = []; self.run = False

    def read(self):
        out = subprocess.run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout
        return sum(float(x) for x in out.split() if x.replace(".", "", 1).isdigit())

    def _loop(self):
        while self.run:
            try: self.samples.append(self.read())
            except Exception: pass
            time.sleep(0.2)

    def start(self):
        if self.ok:
            self.run = True; self.t = threading.Thread(target=self._loop, daemon=True); self.t.start()

    def stop(self):
        if self.ok:
            self.run = False; self.t.join(); return float(np.mean(self.samples)) if self.samples else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--m", type=int, default=150, help="test points (token boundaries) spread over the text")
    ap.add_argument("--ctx", type=int, default=800, help="characters of preceding text in each prompt")
    ap.add_argument("--gen", type=int, default=12, help="tokens the big model writes per call")
    a = ap.parse_args()

    tr = json.load(open(os.path.join(HERE, "data", "spark_trace.json")))
    text = base64.b64decode(tr["text_b64"]); s = text.decode("latin-1")
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)

    ends = sorted(m.end() - 1 for m in PRETOK.finditer(s))
    cand = [e for e in ends if 1500 <= e < len(text) - 200]
    pts = set(cand[int(k)] for k in np.linspace(0, len(cand) - 1, a.m))

    # 1) SPARK reads the text; at each test point it drafts its own continuation (feeding back its own guesses)
    print("SPARK reading the text and drafting at", len(pts), "points ...", flush=True)
    g = g2.GoldenV2(W, cfg, tb=12, lut=lut); drafts = {}
    for i, b in enumerate(text):
        o = g.step(int(b))
        if i in pts:
            h = copy.deepcopy(g); d, c, nxt, cc = [], [], o["pred"], o["conf"]
            for _ in range(48):
                d.append(nxt); c.append(cc / 255.0)
                oo = h.step(int(nxt)); nxt, cc = oo["pred"], oo["conf"]
            drafts[i] = (bytes(d), c)
    print("SPARK done.", flush=True)

    # 2) the big model writes its continuation at the same points
    print(f"model {a.model}: warming up ...", flush=True)
    p0 = min(pts); ollama(a.host, a.model, s[max(0, p0 - a.ctx):p0 + 1], 2)
    ps = ollama_ps(); print(ps.strip(), flush=True)
    on_gpu = ("GPU" in ps) and ("100% CPU" not in ps)
    pm = PowerMeter(); idle = None
    if pm.ok:
        time.sleep(2); idle = float(np.mean([pm.read() for _ in range(5)]))
    pm.start(); big = {}; ev_tok = ev_ns = 0; t0 = time.time()
    for k, i in enumerate(sorted(pts)):
        r = ollama(a.host, a.model, s[max(0, i - a.ctx):i + 1], a.gen)
        out = r.get("response", "")
        cut = next((j for j, ch in enumerate(out) if ord(ch) > 255), len(out))
        big[i] = out[:cut].encode("latin-1")
        ev_tok += r.get("eval_count", 0); ev_ns += r.get("eval_duration", 0)
        if k % 25 == 0:
            print(f"  {k}/{len(pts)}  {(time.time()-t0)/(k+1):.1f} s per call", flush=True)
    dt = time.time() - t0; avg_p = pm.stop()
    s_per_tok = ev_ns / 1e9 / max(1, ev_tok)

    # 3) score at token level
    rows = []
    for i in sorted(pts):
        truth = pieces(text[i + 1:i + 200])[:a.gen]; gpu = pieces(big[i])
        dr, dc = drafts[i]; spp = pieces(dr)
        rows.append({"i": i, "truth": truth, "gpu": gpu, "spark": spp, "draft": dr, "dconf": dc})

    def first(p):
        return p[0] if p else b""

    n = len(rows)
    gpu_tok_acc = np.mean([first(r["gpu"]) == first(r["truth"]) for r in rows])
    sp_tok_acc = np.mean([first(r["spark"]) == first(r["truth"]) for r in rows])
    agree = np.mean([first(r["spark"]) == first(r["gpu"]) for r in rows])
    res = {"model": a.model, "points": n, "ollama_ps": ps, "on_gpu": on_gpu, "seconds_per_call": dt / n,
           "seconds_per_generated_token": s_per_tok, "gpu_idle_W": idle, "gpu_avg_W": avg_p,
           "next_token_accuracy_big": float(gpu_tok_acc), "next_token_accuracy_spark": float(sp_tok_acc),
           "spark_agrees_with_big_next_token": float(agree), "answer_mode": [], "draft_mode": [], "router": []}
    print(f"\nnext-token accuracy (vs real code): big model {gpu_tok_acc:.1%} | SPARK {sp_tok_acc:.1%} | "
          f"SPARK agrees with big model {agree:.1%}  ({n} points)")

    print("\nANSWER MODE (SPARK answers the next token when P(whole token right) = product of its byte confidences >= tau)")
    for tau in (0.3, 0.5, 0.7, 0.9):
        kept = [r for r in rows if r["spark"] and float(np.prod(r["dconf"][:len(r["spark"][0])])) >= tau]
        kf = len(kept) / n
        ag = np.mean([first(r["spark"]) == first(r["gpu"]) for r in kept]) if kept else float("nan")
        acc = np.mean([(first(r["spark"]) if r in kept else first(r["gpu"])) == first(r["truth"]) for r in rows])
        res["answer_mode"].append({"tau": tau, "tokens_kept_by_spark": kf, "agree_with_big": float(ag), "system_token_acc": float(acc)})
        print(f"  conf>={tau}: SPARK answers {kf:5.1%} of tokens, agrees with big model on {ag:5.1%} of them; "
              f"system accuracy {acc:.1%} (big alone {gpu_tok_acc:.1%})")

    print("\nDRAFT MODE (lossless greedy speculative decoding: big model checks SPARK's draft in one call)")
    for th in (0.05, 0.1, 0.2, 0.3):
        toks = []
        for r in rows:
            cum, j = 1.0, 0
            while j < len(r["draft"]) and cum * r["dconf"][j] >= th:
                cum *= r["dconf"][j]; j += 1
            draft = r["draft"][:j]; acc_tok = 0; pos = 0
            for p in r["gpu"]:                       # whole tokens of the big model's output covered by the draft
                if draft[pos:pos + len(p)] == p:
                    acc_tok += 1; pos += len(p)
                else:
                    break
            toks.append(acc_tok + 1)                 # + the token the big model writes itself
        tpp = float(np.mean(toks))
        res["draft_mode"].append({"theta": th, "tokens_per_big_pass": tpp})
        print(f"  draft threshold {th}: {tpp:.2f} tokens per big-model pass (big model alone: 1.00) -> {tpp:.2f}x fewer passes")

    print("\nROUTER (SPARK rates 10 groups of test points by its confidence; easiest groups served by SPARK alone)")
    rs = sorted(rows, key=lambda r: r["i"]); grp = np.array_split(np.arange(n), 10)
    gconf = [np.mean([np.mean(rs[j]["dconf"][:8]) for j in G]) for G in grp]
    order = np.argsort(gconf)[::-1]
    for f in (1, 3, 5):
        sel = [j for gi in order[:f] for j in grp[gi]]
        sa = np.mean([first(rs[j]["spark"]) == first(rs[j]["truth"]) for j in sel])
        ba = np.mean([first(rs[j]["gpu"]) == first(rs[j]["truth"]) for j in sel])
        res["router"].append({"groups": f, "spark_acc": float(sa), "big_acc": float(ba)})
        print(f"  easiest {f*10}% of groups: SPARK alone {sa:.1%} vs big model {ba:.1%}")

    print("\nENERGY")
    if on_gpu and avg_p and idle is not None and avg_p > idle + 5:
        j_tok = avg_p * s_per_tok
        res["joules_per_big_token"] = j_tok
        print(f"  measured on your GPU: {avg_p:.0f} W while generating, {s_per_tok*1000:.0f} ms per token -> {j_tok:.2f} J per token")
        for row in res["answer_mode"]:
            f = 1 - row["tokens_kept_by_spark"]
            print(f"  answer mode conf>={row['tau']}: {j_tok:.2f} J -> {j_tok*f:.2f} J per token ({1/max(f,1e-9):.2f}x less)")
    else:
        print("  not reported: the model is not running on an NVIDIA GPU (see `ollama ps` above), so GPU power does not "
              f"reflect the work. CPU time per generated token: {s_per_tok*1000:.0f} ms.")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    fn = os.path.join(HERE, "out", "local_llm2_%s.json" % re.sub(r"[^A-Za-z0-9_.-]", "_", a.model))
    for r in rows:
        for k in ("truth", "gpu", "spark"):
            r[k] = [p.decode("latin-1") for p in r[k]]
        r["draft"] = r["draft"].decode("latin-1")
    res["rows"] = rows
    json.dump(res, open(fn, "w"), indent=1)
    print("\nsaved", fn)


if __name__ == "__main__":
    main()
