"""RL-rollout drafting: the AI-development workload (GRPO/PPO-style: G sampled completions per prompt).

Why this matters: RL post-training samples many completions of the same prompt, and repeats prompts across steps.
Sibling rollouts share phrases, so a recall memory shared by all streams (SPARK v2 GoldenV2Multi: per-stream
network state, shared recall tables + LUT) should draft far better than for a single isolated request.

Acceptance with sampling (temperature T): for a deterministic draft, speculative sampling accepts draft token d with
probability p(d), so P(the realised sample equals the draft prefix) = expected acceptance of that prefix. Matching
drafts against the realised rollout is therefore an unbiased estimate of lossless speculative-sampling acceptance.

Scenarios
  parallel : the G rollouts of a prompt are generated together, byte-interleaved (one batched decode)
  repeat   : the same prompt was already rolled out G times in an earlier RL step (history available)
Drafters
  copy-own   : host prompt-lookup over prompt + own rollout (software baseline used by serving stacks)
  copy-sib   : host suffix lookup over prompt + all sibling rollouts so far (strong software baseline)
  spark-own  : SPARK with private recall tables
  spark-shared: SPARK with recall tables shared by all sibling streams
  best       : tree verification of copy-sib + spark-shared
GPU stand-in: byte-level nanoGPT (out_big). Tokens = GPT-2-style word pieces. SIMULATED (stand-in model)."""
import copy, json, os, re, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "golden"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
from model import GPT, GPTConfig  # noqa
PRETOK = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z_]+| ?[0-9]+| ?[^\sA-Za-z_0-9]+|\s+(?!\S)|\s+""")
NP, G, RL, TEMP, DL, EVERY = int(os.environ.get("NP", 10)), 8, 160, float(os.environ.get("TEMP", 0.8)), 32, 3


def pieces(b):
    return [x.group(0).encode("latin-1") for x in PRETOK.finditer(b.decode("latin-1"))]


def acc(draft, target):
    """whole target pieces covered by the draft, + 1 bonus token from the verifying pass"""
    n, pos = 0, 0
    for p in pieces(target)[:-1]:
        if draft[pos:pos + len(p)] == p:
            n += 1; pos += len(p)
        else:
            break
    return n + 1


def copy_from(hists, ctx, nmax=32, nmin=3):
    """longest suffix match; hists[0] is the stream's own text (its final, trivial match is excluded)"""
    for N in range(min(nmax, len(ctx)), nmin - 1, -1):
        key = ctx[-N:]
        for i, h in enumerate(hists):
            j = (h[:-1] if i == 0 else h).rfind(key)
            if j >= 0 and j + N < len(h):
                return h[j + N:j + N + DL]
    return b""


def main():
    torch.manual_seed(0)
    Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); text = bytes(Z["test_text"])
    lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
    cfg = g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
    ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
    s = text.decode("latin-1")
    starts = [x.end() for x in PRETOK.finditer(s) if 2000 < x.end() < len(text) - 200]
    starts = [starts[int(k)] for k in np.linspace(0, len(starts) - 1, NP)]
    res = {sc: {d: [] for d in ("copy-own", "copy-sib", "spark-own", "spark-shared", "best")} for sc in ("parallel", "repeat")}

    def rollouts(prompt):
        seq = torch.tensor(list(prompt[-128:]))[None].repeat(G, 1)
        with torch.no_grad():
            for _ in range(RL):
                lg, _ = m(seq[:, -128:])
                nxt = torch.multinomial(torch.softmax(lg[:, -1].float() / TEMP, -1), 1)
                seq = torch.cat([seq, nxt], 1)
        return [bytes(r[-RL:].tolist()) for r in seq]

    def sdraft(st, first):
        h = copy.deepcopy(st); d = [first]
        for _ in range(DL - 1):
            d.append(h.step(int(d[-1]))["pred"])
        return bytes(d)

    for pi, st in enumerate(starts):
        prompt = text[st - 400:st]
        R = rollouts(prompt)
        for sc in ("parallel", "repeat"):
            prev = rollouts(prompt) if sc == "repeat" else []          # an earlier RL step on the same prompt
            own = [g2.GoldenV2(W, cfg, tb=12, lut=lut) for _ in range(G)]
            sh = g2.GoldenV2Multi(W, cfg, ns=G, tb=12, lut=lut)
            for r in prev:                                             # earlier step's rollouts were seen by the shared memory
                for b in prompt[-8:] + r:
                    sh.step(0, b)
            for b in prompt:                                           # every stream reads the prompt
                for j in range(G):
                    own[j].step(b)
                for j in range(G):
                    sh.step(j, b)
            bounds = [set(x.end() - 1 for x in PRETOK.finditer(R[j].decode("latin-1"))) for j in range(G)]
            cnt = [0] * G
            for t in range(RL - DL):
                for j in range(G):
                    oo = own[j].step(R[j][t]); os_ = sh.step(j, R[j][t])
                    if t not in bounds[j]:
                        continue
                    cnt[j] += 1
                    if cnt[j] % EVERY:
                        continue
                    target = R[j][t + 1:t + 1 + DL]
                    mine = prompt + R[j][:t + 1]
                    sib = [mine] + [R[k][:t + 1 if k < j else t] for k in range(G) if k != j] + prev
                    dco, dcs = copy_from([mine], mine), copy_from(sib, mine)
                    dso, dss = sdraft(own[j], oo["pred"]), sdraft(sh.s[j], os_["pred"])
                    a = {"copy-own": acc(dco, target) if dco else 1, "copy-sib": acc(dcs, target) if dcs else 1,
                         "spark-own": acc(dso, target), "spark-shared": acc(dss, target)}
                    a["best"] = max(a["copy-sib"], a["spark-shared"])
                    for k, v in a.items():
                        res[sc][k].append(v)
        print(f"prompt {pi+1}/{NP}: " + "  ".join(f"{sc}:" + ",".join(f"{np.mean(v):.2f}" for v in res[sc].values()) for sc in res), flush=True)
    out = {"temperature": TEMP, "G": G, "prompts": NP, "points": {sc: len(res[sc]["best"]) for sc in res},
           "tokens_per_pass": {sc: {k: float(np.mean(v)) for k, v in res[sc].items()} for sc in res}}
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(HERE, "..", "results", f"rollout_draft_T{TEMP}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
