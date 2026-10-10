#!/usr/bin/env python3
"""SPARK beside a REAL big model on your own PC (Ollama), standard-library Python only.

What it does
  1. Loads data/spark_trace.json: held-out Python code + SPARK v2's exact per-byte outputs (prediction, confidence).
  2. Asks your local model (e.g. a 9B or 14B model in Ollama) for its greedy next byte at N positions of the same text
     (raw completion, temperature 0, prompt = up to --ctx preceding characters).
  3. Measures your GPU's real power with nvidia-smi while it works (NVIDIA only; skipped otherwise).
  4. Reports, against the big model:
       - answer mode: when SPARK is confident, how often it agrees with the big model, and how many big-model calls are saved
       - draft mode (lossless): bytes accepted per big-model call when SPARK drafts and the big model checks
       - router: SPARK's easiest chunks vs the big model
       - measured joules per big-model call and the energy saved
Usage
  ollama pull <model>          (e.g. qwen2.5-coder:7b, gemma2:9b, qwen2.5:14b, deepseek-coder-v2 ... any you have)
  python3 hw/system/local_llm_test.py --model <model> [--n 2000]
  Send back: the printed summary, or hw/system/out/local_llm_result_<model>.json
"""
import argparse, base64, json, os, re, shutil, subprocess, threading, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")


def ollama(host, model, prompt, timeout=300):
    body = json.dumps({"model": model, "prompt": prompt, "raw": True, "stream": False, "think": False,
                       "keep_alive": "30m",
                       "options": {"temperature": 0, "top_k": 1, "num_predict": 1, "num_ctx": 4096, "seed": 0}}).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


class PowerMeter:
    def __init__(self):
        self.ok = shutil.which("nvidia-smi") is not None
        self.samples, self.run = [], False

    def read(self):
        out = subprocess.run(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout
        return sum(float(x) for x in out.split() if x.replace(".", "", 1).isdigit())

    def _loop(self):
        while self.run:
            try:
                self.samples.append(self.read())
            except Exception:
                pass
            time.sleep(0.2)

    def start(self):
        if self.ok:
            self.samples, self.run = [], True
            self.t = threading.Thread(target=self._loop, daemon=True); self.t.start()

    def stop(self):
        if self.ok:
            self.run = False; self.t.join()
            return sum(self.samples) / max(1, len(self.samples))
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--n", type=int, default=2000, help="positions to test (more = slower, more precise)")
    ap.add_argument("--start", type=int, default=2000, help="first test position in the 20,000-byte text")
    ap.add_argument("--ctx", type=int, default=1500, help="characters of preceding text given to the model")
    a = ap.parse_args()

    tr = json.load(open(os.path.join(HERE, "data", "spark_trace.json")))
    text = base64.b64decode(tr["text_b64"])
    sp = bytes.fromhex(tr["pred_hex"]); conf = [c / 255 for c in bytes.fromhex(tr["conf_hex"])]
    s = text.decode("latin-1")
    pos = list(range(a.start, min(a.start + a.n, len(text) - 1)))

    print(f"model {a.model}: warming up ...", flush=True)
    ollama(a.host, a.model, s[pos[0] - a.ctx:pos[0] + 1])
    pm = PowerMeter()
    idle = None
    if pm.ok:
        time.sleep(2); idle = sum(pm.read() for _ in range(5)) / 5
        print(f"GPU idle power {idle:.0f} W", flush=True)
    big = {}
    pm.start(); t0 = time.time()
    for k, i in enumerate(pos):
        chunk0 = i - (i - a.start) % 256                   # stable prompt prefix per 256 positions (KV-cache reuse)
        lo = max(0, chunk0 - a.ctx)
        r = ollama(a.host, a.model, s[lo:i + 1])
        out = r.get("response", "")
        big[i] = ord(out[0]) if out and ord(out[0]) < 256 else -1
        if k % 100 == 0:
            print(f"  {k}/{len(pos)}  {(time.time()-t0)/(k+1):.2f} s per call", flush=True)
    dt = time.time() - t0
    avg_p = pm.stop()
    calls = len(pos)
    j_call = (avg_p * dt / calls) if avg_p else None

    truth = {i: text[i + 1] for i in pos}
    big_acc = sum(big[i] == truth[i] for i in pos) / calls
    sp_acc = sum(sp[i] == truth[i] for i in pos) / calls
    res = {"model": a.model, "positions": calls, "seconds_per_call": dt / calls, "big_model_accuracy": big_acc,
           "spark_accuracy": sp_acc, "gpu_idle_W": idle, "gpu_avg_W_during_test": avg_p, "joules_per_big_call": j_call,
           "answer_mode": [], "draft_mode": [], "router": []}
    print(f"\nbig model accuracy {big_acc:.1%} | SPARK accuracy {sp_acc:.1%} | {dt/calls:.2f} s per big-model call"
          + (f" | measured {j_call:.1f} J per big-model call (avg {avg_p:.0f} W)" if j_call else ""))

    # token boundaries (approximate BPE) for token-level counting
    ends = set(m.end() - 1 for m in PRETOK.finditer(s))
    print("\nANSWER MODE (SPARK answers when confident; the big model answers the rest)")
    for tau in (0.6, 0.7, 0.8, 0.9, 0.95):
        kept = [i for i in pos if conf[i] >= tau]
        agree = sum(sp[i] == big[i] for i in kept) / max(1, len(kept))
        sys_acc = sum((sp[i] if conf[i] >= tau else big[i]) == truth[i] for i in pos) / calls
        # big-model calls: one per LLM token that contains any unconfident byte
        tok_need, cur, ntok = 0, False, 0
        for i in pos:
            cur = cur or conf[i] < tau
            if (i + 1) in ends:
                ntok += 1; tok_need += cur; cur = False
        frac = tok_need / max(1, ntok)
        row = {"tau": tau, "bytes_kept_by_spark": len(kept) / calls, "agreement_with_big_model": agree,
               "system_accuracy": sys_acc, "big_calls_per_token": frac}
        res["answer_mode"].append(row)
        print(f"  conf>={tau}: SPARK keeps {len(kept)/calls:5.1%} of bytes, agrees with big model on {agree:5.1%} of them; "
              f"system accuracy {sys_acc:.1%} (big alone {big_acc:.1%}); big-model calls per token {frac:.2f}")

    print("\nDRAFT MODE (lossless: SPARK drafts while confident, the big model checks in one call)")
    for tau in (0.6, 0.7, 0.8, 0.9):
        k, calls_d, bytes_out = 0, 0, 0
        while k < len(pos):
            j = 0
            while k + j < len(pos) and conf[pos[k + j]] >= tau and j < 24:
                j += 1
            acc = 0
            while acc < j and sp[pos[k + acc]] == big[pos[k + acc]]:
                acc += 1
            k += acc + 1; calls_d += 1; bytes_out += acc + 1
        row = {"tau": tau, "bytes_per_big_call": bytes_out / calls_d}
        res["draft_mode"].append(row)
        print(f"  conf>={tau}: {bytes_out/calls_d:.2f} bytes per big-model call (big model alone: 1 byte-step per call)")

    print("\nROUTER (SPARK rates 128-byte chunks; easiest chunks served by SPARK alone)")
    C = 128; chunks = [pos[x:x + C] for x in range(0, len(pos) - C + 1, C)]
    mc = sorted(((sum(conf[i] for i in ch) / C, ch) for ch in chunks), key=lambda t: -t[0])
    for f in (0.1, 0.25, 0.5):
        e = [ch for _, ch in mc[:max(1, int(f * len(mc)))]]
        sa = sum(sp[i] == truth[i] for ch in e for i in ch) / (C * len(e))
        ba = sum(big[i] == truth[i] for ch in e for i in ch) / (C * len(e))
        res["router"].append({"fraction": f, "spark_acc": sa, "big_acc": ba})
        print(f"  easiest {f:.0%} of chunks: SPARK alone {sa:.1%} vs big model {ba:.1%}")

    if j_call:
        print("\nMEASURED ENERGY on your GPU (per byte-step of the big model)")
        for row in res["answer_mode"]:
            saved = 1 - row["bytes_kept_by_spark"]
            print(f"  conf>={row['tau']}: {j_call:.1f} J -> {j_call*saved:.1f} J per byte "
                  f"({1/max(saved,1e-9):.2f}x less), SPARK adds ~0.00000002 J")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    fn = os.path.join(HERE, "out", "local_llm_result_%s.json" % re.sub(r"[^A-Za-z0-9_.-]", "_", a.model))
    json.dump(res, open(fn, "w"), indent=1)
    print("\nsaved", fn)


if __name__ == "__main__":
    main()
