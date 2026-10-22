# Prior art: speculative decoding from lookup tables (no neural draft model)

Source: two outside answers (to the same prompt) with links to the papers. I have not opened the papers; all figures are second-hand.
Unit: MAT = mean tokens committed per target pass, bonus token included, plain decoding = 1.0. This is the same unit as our `acc()` count (matched pieces + 1).

## Published numbers (token level, real models)

| Method | Target / hardware | Text | MAT (tokens per pass) | Measured speed-up |
|---|---|---|---|---|
| Prompt lookup | Llama-3.1-8B, H100 | coding | 1.91 | 1.71x |
| | | writing | 1.39 | 1.23x |
| | | roleplay | 1.21 | 1.06x |
| | | summarisation | 1.82 | 1.63x |
| | | mixed overall | 1.61 | 1.45x |
| SuffixDecoding (linear, standalone) | same | coding / writing / roleplay / summarisation | 1.98 / 1.44 / 1.25 / 1.73 | 1.83x / 1.33x / 1.16x / 1.62x |
| | same | agentic SWE-Bench / AgenticSQL | 7.8 / 6.3 | 5.3x on AgenticSQL |
| Prompt lookup | Mistral-7B, A100 | summarisation, context QA | not found | 2.4x average (author-measured) |
| REST (27 GB code or 12 GB chat datastore) | CodeLlama-7B | HumanEval code | 2.65 | 2.36x |
| | Vicuna-7B/13B | MT-Bench chat | not found | 1.62-1.77x |
| SAM-Decoding (suffix automaton) | Vicuna-7B | mixed / code / context QA | 2.30 / 2.64 / 2.44 | 1.84x / 2.29x / 2.24x |
| vLLM n-gram | Qwen3-8B reasoning | GPQA / AIME | 4.2 / 3.5 (including bonus) | 1.5-1.58x |

Discrepancy between the two answers: one quotes "10.41x" for SuffixDecoding on AgenticSQL, the other 5.3x for the standalone linear version; I use the lower, paper-level number. A vendor blog quoting 22-40% draft acceptance and ~1.15x for enterprise n-gram speculation is a weaker source.

## What was not found

- No FPGA or ASIC drafter that is purely lookup-based (no neural draft model). The FPGA work found uses a small neural draft model.
- No controlled speed-up on non-repetitive prose; the closest are the writing and roleplay categories above (1.06-1.33x).

## What it means for us

1. **Our measured copy-lookup result is in line with the literature.** On Python source with the 3B model we measured 2.12-2.16 tokens per pass with copy lookup (2.28 with all drafters), against 1.9-2.0 published for coding with an 8B model. Ours is a more repetitive corpus and a different protocol, so this is "same ballpark", not "better".
2. **On non-repetitive writing, lookup drafting gives about 1.2-1.4 tokens per pass** (6-33% speed-up) in the published data. That bounds what any lookup design can promise for prose; our byte-level prose accuracy (44%) cannot be compared directly.
3. **The strongest published case is repetitive agent workloads** (6-8 tokens per pass with a global suffix store). This matches our AI-development angle: agent loops and RL rollouts repeat heavily. It is also what SuffixDecoding already does in software on a CPU, so a hardware version must win on energy, offload or many-stream scale, not on speed of search.
4. **Hardware novelty is plausible but unproven:** nothing published, which can mean open ground or no demand.
5. **Our byte-level core must become token-level** for a real LLM: tables keyed by token IDs (value about 18 bits, entry about 33 bits), drafting by chaining lookups. A draft of 8 tokens would take about 40 cycles (about 1.5 microseconds at 27 MHz) against 19-72 ms per target step, so speed is not the constraint.

## Next test (written, needs your PC)

`hw/system/token_lookup_test.py` measures MAT on a real model for code and prose, for prompt lookup, hashed tables with hysteresis counters (the L-lookup design at token level) and both together. Plumbing and the simulation logic are checked on synthetic streams here (perfect repetition 8.3, random 1.0); the real numbers need a model.
