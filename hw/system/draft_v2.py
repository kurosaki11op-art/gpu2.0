"""Draft mode, round 2 (chip design unchanged; host-side drafting policy only).
SPARK drafts bytes; the GPU model checks the whole draft in one pass, keeps the longest prefix equal to its own greedy
output and adds one byte (or token) of its own. Output is identical to the GPU alone (lossless).
Metric: output bytes per GPU pass (higher = fewer GPU passes). Policies:
  per-byte  : draft while each byte's calibrated confidence >= tau (round 1)
  cumulative: draft while the product of confidences (P(whole draft right)) >= theta
  tokens    : only whole LLM tokens count (BPE GPU) vs bytes (token healing / byte-level GPU)
  oracle    : SPARK drafts exactly while it agrees with the GPU (upper bound for SPARK's predictions)"""
import json, os, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")


def run(sp, conf, gp, ends, policy, th, K, whole_tokens):
    n = len(gp) - 1; i = steps = 0; out_b = 0; drafted = 0
    while i < n:
        j, cum = 0, 1.0
        while j < K and i + j < n:
            c = conf[i + j]
            if policy == "per-byte" and c < th: break
            if policy == "cumulative":
                if cum * c < th: break
                cum *= c
            if policy == "oracle" and sp[i + j] != gp[i + j]: break
            j += 1
        drafted += j
        acc = 0
        while acc < j and sp[i + acc] == gp[i + acc]:
            acc += 1
        k = acc
        if whole_tokens:
            while k > 0 and not ends[i + k]:
                k -= 1
        i += k
        # bonus: the GPU's own next byte (byte-level) or next whole token
        if whole_tokens:
            while i < n:
                i += 1
                if ends[i]: break
        else:
            i += 1
        steps += 1
    return {"bytes_per_pass": n / steps, "draft_bytes_per_pass": drafted / steps}


res = {}
for split in ("cal", "test"):
    d = Z[f"{split}_text"]; sp = Z[f"{split}_sp"]; conf = Z[f"{split}_conf"]; gp = Z[f"{split}_big_pred"]
    ends = np.zeros(len(d) + 1, bool)
    for m in PRETOK.finditer(bytes(d).decode("latin-1")):
        ends[m.end() - 1] = True
    bpt = len(d) / ends.sum()
    base = run(sp, conf, gp, ends, "none", 0, 0, True)["bytes_per_pass"]
    rows = {}
    for wt in (True, False):
        tag = "tokens" if wt else "bytes"
        for pol, ths in (("per-byte", (0.5, 0.6, 0.7, 0.8, 0.9)), ("cumulative", (0.1, 0.2, 0.3, 0.5, 0.7)), ("oracle", (0,))):
            for th in ths:
                for K in (8, 16, 32, 64):
                    r = run(sp, conf, gp, ends, pol, th, K, wt)
                    rows[f"{tag}|{pol}|{th}|{K}"] = r
    res[split] = {"gpu_only_bytes_per_pass_tokens": base, "bytes_per_token": bpt, "rows": rows}
# choose policy settings on cal, report on test
print("GPU alone: 1 token per pass ({:.2f} bytes/pass)".format(res["test"]["gpu_only_bytes_per_pass_tokens"]))
for tag in ("tokens", "bytes"):
    for pol in ("per-byte", "cumulative", "oracle"):
        cand = {k: v for k, v in res["cal"]["rows"].items() if k.startswith(f"{tag}|{pol}|")}
        best = max(cand, key=lambda k: cand[k]["bytes_per_pass"])
        t = res["test"]["rows"][best]; gpu = res["test"]["gpu_only_bytes_per_pass_tokens"] if tag == "tokens" else 1.0
        print(f"{tag:6s} {pol:10s} best on cal = {best.split('|',2)[2]:8s} -> test {t['bytes_per_pass']:.2f} bytes/pass "
              f"({t['bytes_per_pass']/gpu:.2f}x fewer GPU passes than GPU alone; drafts {t['draft_bytes_per_pass']:.1f} bytes)")
json.dump(res, open(os.path.join(HERE, "..", "results", "draft_v2.json"), "w"), indent=1)


def run_heal(sp, conf, gp, ends, th, K):
    """Token healing: accepted bytes count even mid-token; the GPU's own contribution is the rest of the current token
    (next pass starts from a prefix-constrained token)."""
    n = len(gp) - 1; i = steps = 0
    while i < n:
        j, cum = 0, 1.0
        while j < K and i + j < n and cum * conf[i + j] >= th:
            cum *= conf[i + j]; j += 1
        acc = 0
        while acc < j and sp[i + acc] == gp[i + acc]:
            acc += 1
        i += acc
        while i < n:                      # GPU completes the current token
            i += 1
            if ends[i]: break
        steps += 1
    return n / steps


Zt = Z
d = Zt["test_text"]; ends = np.zeros(len(d) + 1, bool)
for m_ in PRETOK.finditer(bytes(d).decode("latin-1")):
    ends[m_.end() - 1] = True
agree = np.mean(Zt["test_sp"][:-1] == Zt["test_big_pred"][:-1])
print(f"\nSPARK agrees with the GPU model on {agree:.1%} of bytes")
for th in (0.1, 0.2, 0.3):
    b = run_heal(Zt["test_sp"], Zt["test_conf"], Zt["test_big_pred"], ends, th, 32)
    print(f"token healing, cumulative {th}: {b:.2f} bytes/pass = {b/res['test']['gpu_only_bytes_per_pass_tokens']:.2f}x fewer GPU passes")
