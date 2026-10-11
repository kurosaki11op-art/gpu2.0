#!/usr/bin/env python3
"""SPARK beside a real big model on your PC (Ollama) -- test v3.

New over v2: (1) new drafters: copy-drafting from the longest earlier match (hardware: recall entries keep a pointer
into a history buffer) and multi-drafting (best of several drafts checked in one pass); (2) answer mode with a learned
token-type gate that learns online from the big model's answers, like SPARK's on-chip calibration counters;
(3) --num-gpu to force the model onto the GPU and measured joules per token; (4) estimated generation speed-up.

Needs: Python 3, numpy. Run:
  python hw/system/local_llm_test3.py --model qwen3.5:9b
  python hw/system/local_llm_test3.py --model <smaller model> --num-gpu 99      (fully on GPU, for energy)
"""
import argparse, base64, copy, json, os, re, shutil, subprocess, sys, threading, time, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden as g1          # noqa: E402
import spark_golden_v2 as g2       # noqa: E402
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
L = 48


def pieces(b):
    return [m.group(0).encode("latin-1") for m in PRETOK.finditer(b.decode("latin-1"))]


def ollama(host, model, prompt, n_tokens, num_gpu, timeout=1800):
    opts = {"temperature": 0, "top_k": 1, "num_predict": n_tokens, "num_ctx": 4096, "seed": 0}
    if num_gpu is not None:
        opts["num_gpu"] = num_gpu
    body = json.dumps({"model": model, "prompt": prompt, "raw": True, "stream": False, "think": False,
                       "keep_alive": "60m", "options": opts}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout
    except Exception as e:
        return f"({' '.join(cmd)} failed: {e})"


class PowerMeter:
    def __init__(self):
        self.ok = shutil.which("nvidia-smi") is not None; self.samples = []; self.run = False

    def read(self):
        out = run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"])
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


def tclass(tok, history):
    t = tok.decode("latin-1")
    if t.strip() == "": c = "space"
    elif re.fullmatch(r" ?[A-Za-z_]+", t): c = "name"
    elif re.fullmatch(r" ?[0-9]+", t): c = "number"
    else: c = "punct"
    rep = tok in history
    return f"{c}{'+seen' if rep and c == 'name' else ''}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--m", type=int, default=150)
    ap.add_argument("--ctx", type=int, default=800)
    ap.add_argument("--gen", type=int, default=12)
    ap.add_argument("--num-gpu", type=int, default=None, help="layers on GPU (99 = all); default: Ollama decides")
    a = ap.parse_args()

    tr = json.load(open(os.path.join(HERE, "data", "spark_trace.json")))
    text = base64.b64decode(tr["text_b64"]); s = text.decode("latin-1")
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
    ends = sorted(m.end() - 1 for m in PRETOK.finditer(s))
    cand = [e for e in ends if 1500 <= e < len(text) - 200]
    pts = sorted(set(cand[int(k)] for k in np.linspace(0, len(cand) - 1, a.m)))

    def spark_draft(h, first):
        d, c, nxt, cc = [], [], first[0], first[1]
        for _ in range(L):
            d.append(nxt); c.append(cc / 255.0)
            o = h.step(int(nxt)); nxt, cc = o["pred"], o["conf"]
        return bytes(d), c

    def copy_longest(i):
        for N in range(32, 2, -1):
            j = text.rfind(text[i - N + 1:i + 1], 0, i)
            if j >= 0:
                return text[j + N:j + N + L]
        return b""

    print("SPARK reading the text and drafting ...", flush=True)
    g = g2.GoldenV2(W, cfg, tb=12, lut=lut); drafts = {}; ps_set = set(pts)
    for i, b in enumerate(text):
        o = g.step(int(b))
        if i in ps_set:
            sd, sc = spark_draft(copy.deepcopy(g), (o["pred"], o["conf"]))
            alts = [v for v in dict.fromkeys(g.last_alts) if v != o["pred"]][:2]
            br = [spark_draft(copy.deepcopy(g), (v, 128))[0] for v in alts]
            drafts[i] = {"spark": sd, "conf": sc, "alts": br, "copy": copy_longest(i)}
    print("SPARK done.", flush=True)

    p0 = pts[0]; ollama(a.host, a.model, s[max(0, p0 - a.ctx):p0 + 1], 2, a.num_gpu)
    ps = run(["ollama", "ps"]); print(ps.strip(), flush=True)
    on_gpu = "100% GPU" in ps
    pm = PowerMeter(); idle = None
    if pm.ok:
        time.sleep(2); idle = float(np.mean([pm.read() for _ in range(5)]))
    pm.start(); big = {}; ev_tok = ev_ns = pr_ns = pr_tok = 0; t0 = time.time()
    for k, i in enumerate(pts):
        r = ollama(a.host, a.model, s[max(0, i - a.ctx):i + 1], a.gen, a.num_gpu)
        out = r.get("response", ""); cut = next((j for j, ch in enumerate(out) if ord(ch) > 255), len(out))
        big[i] = out[:cut].encode("latin-1")
        ev_tok += r.get("eval_count", 0); ev_ns += r.get("eval_duration", 0)
        pr_tok += r.get("prompt_eval_count", 0); pr_ns += r.get("prompt_eval_duration", 0)
        if k % 25 == 0:
            print(f"  {k}/{len(pts)}  {(time.time()-t0)/(k+1):.1f} s per call", flush=True)
    avg_p = pm.stop(); s_tok = ev_ns / 1e9 / max(1, ev_tok)

    def acc(draft, gpu):
        n, pos = 0, 0
        for p in pieces(gpu):
            if draft[pos:pos + len(p)] == p:
                n += 1; pos += len(p)
            else:
                break
        return n + 1

    def first(p):
        return p[0] if p else b""

    R = {"model": a.model, "ollama_ps": ps, "on_gpu": on_gpu, "points": len(pts), "seconds_per_token": s_tok}
    tg = [pieces(big[i]) for i in pts]; tt = [pieces(text[i + 1:i + 200])[:a.gen] for i in pts]
    sp = [pieces(drafts[i]["spark"]) for i in pts]
    big_acc = np.mean([first(x) == first(y) for x, y in zip(tg, tt)])
    print(f"\nnext-token accuracy vs real code: big model {big_acc:.1%} | SPARK {np.mean([first(x)==first(y) for x,y in zip(sp,tt)]):.1%} "
          f"| copy {np.mean([first(pieces(drafts[i]['copy']))==first(y) for i,y in zip(pts,tt)]):.1%}")

    print("\nDRAFT MODE (lossless): whole big-model tokens per big-model pass (big model alone = 1.00)")
    D = {}
    for name in ("spark", "copy", "spark+copy", "multi"):
        v = []
        for i in pts:
            d = drafts[i]; gp = big[i]
            cands = {"spark": [d["spark"]], "copy": [d["copy"]], "spark+copy": [d["spark"], d["copy"]],
                     "multi": [d["spark"], d["copy"]] + d["alts"]}[name]
            v.append(max([acc(x, gp) for x in cands if x] or [1]))
        D[name] = float(np.mean(v)); print(f"  {name:11s}: {D[name]:.2f} tokens per pass")
    R["draft"] = D

    print("\nANSWER MODE with a learned token-type gate (learns online from the big model, answers only proven types)")
    R["answer"] = []
    for target in (0.95, 0.9, 0.8):
        cnt = {}; answered = agree = right = 0; hist = b""
        for k, i in enumerate(pts):
            spt = first(sp[k]); gpt = first(tg[k]); tru = first(tt[k])
            cls = tclass(spt, text[max(0, i - 800):i + 1])
            n_, a_ = cnt.get(cls, (0, 0))
            use = n_ >= 5 and a_ / n_ >= target and spt
            out = spt if use else gpt
            answered += bool(use); agree += bool(use) and spt == gpt; right += out == tru
            cnt[cls] = (n_ + 1, a_ + (spt == gpt))                       # feedback from the big model
        n = len(pts)
        row = {"target": target, "answered": answered / n, "agree": agree / max(1, answered), "system_acc": right / n}
        R["answer"].append(row)
        print(f"  gate {target:.0%}: SPARK answers {row['answered']:5.1%} of tokens, agrees {row['agree']:5.1%}; "
              f"system accuracy {row['system_acc']:.1%} (big alone {big_acc:.1%})")

    print("\nSPEED / ENERGY")
    best = max(D.values())
    print(f"  big model: {s_tok*1000:.0f} ms per generated token; with SPARK drafting ({best:.2f} tokens per pass) "
          f"generation needs {1/best:.0%} of the big-model passes -> up to {best:.2f}x faster generation (same output)")
    if on_gpu and avg_p and idle is not None and avg_p > idle + 5:
        j = avg_p * s_tok; R["joules_per_token"] = j
        print(f"  measured: {avg_p:.0f} W -> {j:.2f} J per token alone; ~{j/best:.2f} J per token with SPARK drafting")
    else:
        print("  energy not reported: model not fully on the GPU (needs '100% GPU' in ollama ps; try --num-gpu 99 or a smaller model)")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    fn = os.path.join(HERE, "out", "local_llm3_%s.json" % re.sub(r"[^A-Za-z0-9_.-]", "_", a.model))
    R["rows"] = [{"i": i, "big": big[i].decode("latin-1"), "spark": drafts[i]["spark"].decode("latin-1"),
                  "copy": drafts[i]["copy"].decode("latin-1"), "truth": text[i + 1:i + 120].decode("latin-1")} for i in pts]
    json.dump(R, open(fn, "w"), indent=1); print("\nsaved", fn)


if __name__ == "__main__":
    main()
