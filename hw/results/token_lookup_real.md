# Token-level lookup drafting on a real model (MEASURED on the team's PC)

Model: Qwen/Qwen2.5-Coder-1.5B (base, not instruct), fp16 on the PC's GPU; greedy; 20 prompts x 128 generated tokens per text type; draft up to K = 8 tokens.
Unit: tokens committed per target pass, bonus included (plain decoding = 1.00), computed offline from the model's own greedy output, so it is exact for greedy verification. Raw JSON is on the PC (`hw/results/token_lookup_Qwen_Qwen2.5-Coder-1.5B.json`); numbers transcribed from the console.

| Text | Prompt lookup (free software) | Hashed tables (L-lookup design, token level) | Both, as a 2-branch tree |
|---|---|---|---|
| Code (Python source excerpts) | 2.39 | 2.41 (+0.8%) | 2.48 (+3.8%) |
| Prose (four old books) | 2.21 | 2.29 (+3.6%) | 2.31 (+4.5%) |

**Verdict against the rule fixed before the run:** tie. The tables are within 5% of prompt lookup on both text types (slightly ahead), so they are not a better drafter than free software; any hardware case has to rest on energy, offload or many-stream scale.

Caveats:
1. **Prose acceptance (2.2-2.3) is far above the published 1.2-1.4 for writing.** Likely cause: a small base coder model continuing old prose with greedy decoding tends to repeat itself, and lookup drafting accepts the repeats. Not yet checked: the script now also reports how copyable the output is, and supports `--chat` for an instruct model asked to continue the text.
2. Small sample (2,560 generated tokens per text type); differences of 1-4% are probably within noise.
3. Generation ran at 6-13 tokens/s, so the model may not have been fully in GPU memory; this does not affect the acceptance numbers, only timing.

## Chat run (instruct model) — settles caveat 1

Model: Qwen/Qwen2.5-1.5B-Instruct, `--chat`, fp16 on the PC's GPU, 20 prompts x 128 tokens, K = 8. MEASURED (console).

| Text | Prompt lookup | Hashed tables | Both | Copyable output |
|---|---|---|---|---|
| Code | 1.69 | 1.70 | 1.72 | 24% |
| Prose | 1.04 | 1.04 | 1.04 | 1% |

The earlier prose gain was the base model repeating itself. A chat model answering normally gives lookup
drafting almost nothing on prose (+4%), and only about +70% on code. Conclusion recorded: a drafting helper
cannot be the project. This result triggered the redesign in `docs/cortex_redesign.md`.
