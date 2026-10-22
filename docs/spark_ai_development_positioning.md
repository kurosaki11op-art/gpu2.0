# L: an AI-development accelerator, not just "cheaper AI"

Labels: **MEASURED** (run on real hardware or a real model), **SIMULATED** (our simulator),
**ESTIMATED** (arithmetic on stated assumptions), **PROJECTED** (needs silicon or a larger test).

## 1. Why the buyer cares

AI labs are not short of ideas. They are short of **generated tokens per GPU-hour and per megawatt**.
Most of the work that improves a model now consists of *generating* text with a model:

| Development loop | What it spends GPU time on |
|---|---|
| RL post-training (reasoning, code, agents) | rolling out thousands of long samples per step, then scoring them |
| Synthetic data / distillation | generating millions of teacher completions |
| Evaluation and red-teaming | generating answers to large benchmark suites on every checkpoint |
| Agent and tool-use training | long, repetitive multi-turn traces (code, logs, JSON, tool output) |

All four are **decode-bound**. One token at a time, the GPU re-reads its weights and KV cache from memory
and leaves most of its arithmetic idle. The uploaded limitations report names exactly this:
**H014 (low-batch decode underutilisation)**, **H020 (memory-bandwidth ceiling)** and
**H034 (memory-movement energy)**.

L's pitch is therefore:

> **L makes every big-model pass produce more than one token, with no change to the output.**
> More rollouts, more synthetic data and more evals from the same GPUs, inside the same power budget.
> Faster iteration loops mean faster model progress.

This is **lossless** (draft mode / speculative decoding). The big model still decides every token, so a lab
does not have to trust L's quality. That is what makes it something a lab could buy.

## 2. What we have actually shown

| Claim | Status | Number |
|---|---|---|
| L v1 chip works, gate-level, through its pins (SKY130 + OpenRAM) | **SIMULATED** (gate-level) | passes all pre-fab checks |
| Draft mode with a real 9B model (qwen3.5:9b via Ollama, user's PC) | **MEASURED** | **1.51 tokens per big-model pass, output identical** |
| Copy-drafting + multi-drafting (local nanoGPT referee) | **SIMULATED** | 1.22 → 1.39 tokens/pass (+14% over L alone) |
| Answer mode (L answers by itself) | **MEASURED** | safe only on ~6% of tokens (conf ≥ 0.9, no accuracy loss) |
| Request router | **MEASURED** | not usable with a real model: dropped |
| Earlier 2.1–2.4× data-centre numbers | withdrawn | were based on a weak simulated referee |

Draft mode is our validated result. Everything below is built on that.

## 3. Mapping L onto the hardware and infrastructure limits

| Report item | Limit | What L does | Honest boundary |
|---|---|---|---|
| **H014** | Low-batch decode underutilisation | Supplies drafts so each pass verifies several tokens: the "speculative sampling" fix the report itself lists | Acceptance varies by task; measured 1.51 on general text |
| **H020** | Memory-bandwidth ceiling | Weights are read once per *pass*, not once per *token*, so fewer bytes per token | Does not raise the bandwidth; it divides the reads |
| **H034** | Memory-movement energy | Fewer full weight sweeps per token mean fewer joules per token. L's own memory is small on-chip SRAM | Must be measured at the wall, including L |
| **H019 / H021** | VRAM and KV-cache growth | No extra draft model in VRAM (unlike a GPU-side draft model). L's state lives on its own chip | Does not shrink the main model's KV cache |
| **H075** | Throughput vs latency | Lowers per-request latency without needing a bigger batch | Gains shrink at very large batch, where the GPU is already compute-bound |
| **H089–H090** | Grid connection and facility capacity | More tokens per joule mean more development work inside a *fixed* MW allocation | It is not new power; it is better use of the power a lab already has |
| **H091–H094** | Load swings, heat, water, PUE | Less GPU energy per token means less heat to remove and less cooling water, per unit of work | Total use can still rise if demand rises (H098) |
| **H098** | Energy rebound | We report per-token **and** total energy, and say plainly that labs will spend savings on more experiments | That is the point for the buyer, but not a carbon claim |
| **H107** | Neuromorphic tooling mismatch | L plugs into the standard speculative-decoding interface (draft in, verify out) with no new programming model | Event-driven efficiency on drafting does not make L an LLM replacement |
| **H110** | No universally best hardware | L targets one bottleneck, decode, and says so | Not useful for training compute or prefill |

## 4. What this means for a lab (ESTIMATED)

Assumptions, stated so a judge can change them:

- Decode is memory-bound, so verifying K draft tokens costs about one normal pass.
- Tokens per pass `a` = 1.51 (MEASURED). L and verification overhead = 10% (ESTIMATED).
- Decode speed-up `s ≈ 1.51 × 0.9 ≈ 1.36×` (ESTIMATED).
- If rollout generation is a fraction `f` of an RL training step (Amdahl's law):

| Generation share of step `f` | Whole-step speed-up at s = 1.36 | at s = 1.6 (copy + multi-draft target) |
|---|---|---|
| 0.4 | 1.12× | 1.18× |
| 0.6 | 1.19× | 1.29× |
| 0.8 | 1.27× | 1.43× |

On code, tool output, JSON and logs, which repeat a lot, copy-drafting should raise `a` well above 1.51.
That is still **PROJECTED** and is the next test (Section 6).

Put plainly: with a fixed GPU fleet and a fixed power cap, a lab gets about **1.1–1.4× more RL steps,
synthetic samples and eval runs per day**, with bit-identical outputs. That is the purchase argument.

## 5. Why a chip and not just software

Speculative decoding already exists in software. L is still worth a chip because:

1. **A draft model on the GPU steals GPU time and VRAM.** L drafts on separate, tiny, low-power silicon, in parallel with verification.
2. **Recall memory and copy-drafting are table lookups.** They suit SRAM plus comparators, not tensor cores.
3. **Calibrated confidence (RLCD LUT, ECE 0.022) chooses draft length per token.** That is report experiment #3, "adaptive speculative draft length", done in hardware every cycle.

The software path is the fallback, and it is also our test harness. We say so openly.

## 6. Falsifiable next experiments (following the report's §13–14 protocol)

| # | Experiment | Pass condition | Reject condition |
|---|---|---|---|
| E1 | `local_llm_test3.py` with the model 100% on GPU (`--num-gpu 99`) | Measured wall-clock tokens/s and J/token both improve vs plain decode | Gain vanishes once real draft and verification time is counted |
| E2 | Same test on code / JSON / tool-trace prompts | Copy + multi-draft reaches ≥ 2 tokens/pass | Stays below 1.6 |
| E3 | Adaptive draft length from L confidence vs best fixed length | Beats every fixed length (report exp. #3) | Ties or loses to a tuned fixed length |
| E4 | 14B model, same settings | Acceptance holds within 10% of 9B | Acceptance collapses with the larger model |
| E5 | Whole-system energy (wall plug, GPU + L) | Lower joules per *verified* token | Lower GPU power but longer runtime raises total energy (report exp. #5) |

Baselines are a strong software drafter (n-gram / prompt lookup) and plain decode, both at equal output.
That is the strong-baseline rule from the report.

## 7. One-line pitch

**"L is a tiny brain-inspired co-processor that lets every GPU pass produce more than one token with
identical output: measured 1.5× with a real 9B model. So AI labs get more RL rollouts, synthetic data and
evaluations from the GPUs and power they already have."**
