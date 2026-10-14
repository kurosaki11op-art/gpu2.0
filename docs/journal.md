# SPARK journal

One entry per step, newest at the bottom. Each entry: what was asked, what was done, the result (with its label),
and where the files are. Earlier history (9-13 Oct) is summarised in `docs/PROJECT_MEMORY.md` section 3 and in
`git log`.

## 2026-10-14

- **User's real-model chat run** (MEASURED, Qwen2.5-1.5B-Instruct, `--chat`): code 1.69 / 1.70 / 1.72, prose
  1.04 / 1.04 / 1.04 (prompt lookup / tables / both). Recorded in `hw/results/token_lookup_real.md`.
- **Video** the user shared (Instagram reel about a founder asking why pay for a website when AI costs $20):
  watched the frames; the audio could not be transcribed in the container; the user pasted the Tamil-English
  transcript. Point: AI writes code but does not understand the business (UX, SEO, security, indexing, rate
  limiting). Conclusion given: these are judgement limits, not hardware limits; SPARK does not fix them.
- **User rejected the helper direction** ("6% is of no use, go for something big, brain as a chip, brain
  principles only, provable in 6-8 months"). Redesign to SPARK Cortex. `docs/cortex_redesign.md`.
- **First proof** (SIMULATED): random-wiring lookup neurons, then learned features + count memory.
  `hw/results/cortex_proof.md`. Digits in stages 95.6 vs network 19.5; exact merge; few-shot loses.
- **Month 1** (user: "close the accuracy gap"): retina centre-surround, concept cells, sleep with dreams,
  resonator cochlea, 8 loudness levels for sound, Speech Commands added. Results in
  `hw/results/cortex_month1.md`. Best brain part within 1.6 points of the network on all three, keeps it in stages.
- User asked not to use the C: drive: clarified that cloud work does not touch their PC; gave D: drive commands.
- **Month 2 started** (user: "shrink the memory and close the problems"). Findings in
  `hw/results/cortex_month2_log.md`. Paused before the dream-source test (`m2h.py`).
- User asked whether everything is saved: committed all scripts and logs (`hw/brain/experiments/`), the running
  month-2 log, and created this journal, `docs/PROJECT_MEMORY.md` and `CLAUDE.md` so nothing is forgotten.
- User asked which second brain to use: chose this GitHub repo opened as an Obsidian vault (I can write it directly,
  it keeps full history, and Obsidian reads it). Added home page `README.md`, indexes for docs, results, hardware
  and prompts, `hw/brain/README.md`, Related links, and the Obsidian vault config.
- User said "continue": ran test h (dream sources, fast table as the only decision maker). Results in
  `hw/results/cortex_month2_log.md`: memory down 70-160x; count dreams match month 1 on sound (71.1 vs 71.8) but lose
  4 points on digits and 9 on clothing.
- User going to sleep, asked for non-stop work until the evening of 15 Oct. Set an every-2-hours safety check-in
  (routine `trig_01UmL6GjCFHNfqdNTvVqZPZi`, India time, delete after 20:00 IST on 15 Oct). Overnight plan: finish
  month 2 (sleep variants, v3 suite with memory budget, few-shot, merge), then month 3 (integer bit-exact model, RTL).
- Overnight tests i-l (month 2 log): a full night of all-class dreams helps images (concept 8x3-bit: digits 95.3,
  clothing 84.2); chip-honest metaplastic 8-bit rate memory (45 KB) within ~1 pt of exact counts (digits 93.1,
  clothing 78.3), image total 73 KB fits Tang Nano block RAM; low-bit on-chip concept cells failed. New code:
  `hw/brain/rate_memory.py` (RateMemory, ConceptRates).

Related: [Project memory](PROJECT_MEMORY.md), [Home](../README.md)
