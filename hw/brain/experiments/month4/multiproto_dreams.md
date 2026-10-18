---
title: Dreams that keep co-occurrence, and virtual examples for new words
date: 2026-10-16
tags: [month4, dreams, continual-learning, few-shot, simulated]
---
# Multi-prototype dreams and virtual examples (16 Oct 2026, morning)

Research behind it: [weak spots](../../../../docs/research_weak_spots.md). All numbers SIMULATED (exact integer chip model, margin 32, 3 seeds).

## 1. Dreams with K prototypes per class (`hw/brain/cortex_proto.py`, `proto_dreams.py`, `dream_variants.py`)

**Problem.** Learning in 5 stages loses accuracy against learning everything at once (clothing 78.7 vs 83.5, words 82 vs 83)
because a dream draws each code bit independently from its class on-rate and so loses which features occur together.
**Fix tested.** The dream memory keeps K count-sets per class; an example goes to the prototype with the highest normalised
overlap (a shifted counter sum, no divide), a dream picks a prototype in proportion to its example count and then draws bits
from it with the chip's L-bit random draws. Integer, no multiplies.

| Dataset | 5 stages, today (K=1) | K=2 | K=4 | K=8 | all at once (K=1 / K=8) |
|---|---|---|---|---|---|
| clothing | 78.7 | 80.3 | **81.5** | **82.1** | 83.3 / 83.9 |
| digits | 94.9 | 94.1 | 94.7 | 94.8 | 97.0 / 97.2 |
| words | 82.0 | 81.7 | **83.0** | 82.7 | 83.1 / 82.9 |
| dream memory (images) | 0.46 Mbit | 0.92 | 1.84 | 3.69 | |

With floating-point rates (an upper bound) staged clothing reaches 82.4 (K=4) and 83.9 (K=8). Replaying stored real
examples instead (10-20 per class) recovers only 1-2 points; cue-and-complete 1.5-2. Narrower prototype counters lose the
gain (K=4 with 8-bit counters 80.2; K=8 with 7-bit 81.7; 5-bit 77.7).
**Verdict.** +2.8 to +3.4 points staged on clothing, +1 on words, nothing on digits, for 4-8x the dream memory (the
largest memory of the chip): an **optional "high-fidelity dreams" setting for clothing-like data**, not a default; no RTL
(it needs K counter sets and a K-way overlap pass per learned example).

## 2. Clothing encoder ideas from the literature (`clothing_gap.py`) - all rejected

Today 83.4 all at once / 78.6 staged. Histogram-quantile brightness thresholds (same memory): 83.4 / 77.4. Three quantile
channels: 82.8 / 77.9. Coarse 5x5 centre-surround pair (+50% bits): 83.5 / 78.5. Two tables with different encoders summed
(2.5x memory): 84.8 / 79.2. The gap to the network (87.3) is capacity, not these knobs.

## 3. New spoken words from a few recordings (`fewshot_words_aug.py`)

Every new recording is also presented with its word start moved to frames 5 and 7 (virtual examples), then IMPRINT + sleep.
Accuracy over all 10 words (old words 5, new words 5), single view / LOOK AGAIN:

| Recordings per new word | none | virtual examples 5,6,7 |
|---|---|---|
| 1 | 48.2 / 49.2 | 49.5 / **51.1** |
| 2 | 49.5 / 49.7 | 49.6 / **51.7** |
| 5 | 51.4 / 53.5 | 51.0 / **55.5** |

New words alone: 1 recording 11.5 -> 22.2%, 5 recordings 18.1 -> 26.3% (with LOOK AGAIN). A small, cheap gain (+2); the
real gap to a network is a learned word embedding, which this chip does not have.

## 4. Pool-limited prototypes and detectors fitted on all old words (16 Oct, afternoon) - small or no gain

**Shared prototype pool (`cortex_proto_pool.py`, `proto_pool.py`, clothing, 5 stages, 3 seeds, SIMULATED).** A class opens a new prototype only
when no existing one overlaps the example well; all classes share a slot pool. Pool 10 / 20 / 30 / 40 gave 78.9 / 80.3-80.6 /
80.7 / 80.7 at 18 / 26 / 36 / 44 slots used (plain K=1 78.7 at 10, K=2 80.3 at 20, K=4 81.5 at 40). Early classes take the pool before
later ones arrive, and no setting beat plain K=2 or K=4 per slot. **Failure: no memory saving over uniform K.** Choice stays: K=1 default,
K=2 (+1.6, 2x dream memory) or K=4 (+2.8, 4x) as optional settings.

**Sound detectors fitted on words 0-4 instead of 0-1 (`fewshot_words_detectors.py`, 3 seeds, LOOK AGAIN, virtual examples 5,6,7, SIMULATED).**
New words alone: 1 recording 22.2 -> 17.7, 2 recordings 22.0 -> 27.3, 5 recordings 26.3 -> 29.4; all ten words 51.1 / 51.7 / 55.5 ->
50.4 / 53.9 / 57.2. About +2 from 2 recordings up, a loss at 1; near seed noise. Not a rule; fitting the detectors on a broader set of
words before shipping is free (a PC-side choice). The real gap (a word embedding learned on many words) is still open.

## 5. Episodic exemplar memory for new words (18 Oct) - no gain, and where the difficulty is

**Test (`fewshot_exemplar.py`, `fewshot_exemplar2.py`, SIMULATED, 3-5 draws).** Keep the k stored sparse codes of each new word (a hippocampus-like
exemplar memory) and classify by the best cosine overlap, alone (5-way among the new words, chance 20%) and fused with the table (10-way).
5-way, k = 1 / 2 / 5 recordings: table after IMPRINT + short sleep 37.7 / 45.0 / 47.4; exemplar nearest neighbour 35.3 / 45.5 / 48.7.
10-way fusion (new word if its best exemplar overlap exceeds t x the best old-word overlap, t = 0.7 .. 1.1): 45-49%, always below the table alone
(48.2 / 49.5 / 51.4). **Failure: the exemplar memory is no better than the table, and fusing them is worse.**
**What it shows.** Among new words alone the chip already gets 38-47% (chance 20%); the 12-29% "new word" figure in the 10-way test is mostly new words
confused with known words. The limit is the representation (the sound code of a word from 1-5 recordings), not the memory: a better memory rule will not
fix it; only better features (learned from many words) can.

## 6. Where new spoken words fail, and a novelty gate (19 Oct) - no gain

**Breakdown (`newword_breakdown.py`, SIMULATED, 3 draws; chip knows words 0-4, learns 5-9 from k recordings, IMPRINT + short sleep).** New-word test clips: with k = 1 recording, 11% correct, 20% called another new word,
**69% called an OLD word**; with k = 5: 18% correct, 22% another new word, 59% an old word. Old-word clips: 84% kept, 9-10% lost to a new word, 7% confused with another old word.
So the failure is at the old / new boundary: a new word learned from 1-5 recordings cannot outscore five old words that were learned from thousands. Among the new words alone the chip is at 38-47% (chance 20%).
**Novelty gate (`newword_novelty.py`).** Send a clip to the new classes when its best old-class score is below tau x the old words' own mean score: k = 1, all ten words 48.0 (no gate) -> 47.6 / 46.3 / 43.8 / 40.5 / 36.5 for tau = 0.5 / 0.7 / 0.8 / 0.9 / 1.0
(new words 11 -> 13 / 21 / 26 / 30 / 32, old words 84 -> 82 / 71 / 62 / 51 / 41). A pure trade of old for new, total accuracy only falls: the best-old-class score of a new word overlaps that of an old word. **Failure.**

## 7. Neurogenesis for new words (19 Oct, user's idea: grow new units instead of overwriting) - no net gain so far

`neurogenesis_words.py`, `neurogenesis_words2.py`, `neurogenesis_words3.py` (SIMULATED, 2 draws). When the new words arrive, the chip grows 16 extra sound detectors per channel, fitted without labels on the k x 5 new recordings only,
and appends their bits to the code; old rows and old codes are untouched. Results, base (no growth) -> grown:
- **v1 (winner-take-all new detectors, fire on every window):** all ten words 48.5 -> 23.8 (k = 1), 50.1 -> 26.6 (k = 2), 50.1 -> 28.5 (k = 5); new words (10-way) 12.7 -> 35.7, 13.1 -> 43.0, 15.2 -> 52.6; **old words 83 -> 12, 86 -> 11, 84 -> 5**.
  The old rows never saw the new bits, so every clip (old words included) is pulled to the new rows. Among the new words alone: 35.2 -> 36.6, 41.2 -> 43.5, 44.8 -> 52.6.
- **v3 (fire only on a strong match, agreement >= 21 or 23 of 25 bits):** the new bits stay dense (550 / 280 on per clip) and old words still collapse (0.3% / 19%).
- **v2 (a stored buffer of 20 old recordings per old word teaches the old rows the new bits; not the no-stored-examples rule):** without rate scaling old words 13 / 11 / 6% (the on-counts of the new bits come from only 20 clips of thousands, so old dreams never switch them on);
  **with the new bits' on-counts scaled to the class's example count (rate estimate): old words 79 / 80%, all ten words 47.1 (k = 1) and 50.8 (k = 2) vs 48.5 / 50.1 base, new words (10-way) 14.2 / 21.0 vs 12.7 / 13.1.**
**Reading.** Growing units is a sound brain idea and it does carry information about the new words (new-vs-new 5-way up to +7.8 at k = 5 before balancing), but the old / new boundary problem returns the moment the old rows lack statistics for the new bits;
once balanced with a small buffer and rate scaling the net gain over all ten words is +0.7 at k = 2 (within noise). Not adopted. A version that needs no stored old recordings would have to estimate the old words' firing rate on the new detectors without audio (not possible), so growth fits cases where the new classes get their own separate readout, not a shared linear table.

## 8. More new-word fixes tried on 19 Oct (all SIMULATED, 3 draws, IMPRINT + short sleep; none helps)

Baseline all ten words / new words / old words: k = 1: 48.0 / 11.1 / 84.0; k = 2: 50.0 / 12.7 / 86.3; k = 5: 51.5 / 18.5 / 83.6 (single view).
- **Logit adjustment by class size** (`newword_calibration.py`; bias = alpha x (bitlen(n_max) - bitlen(n_c)), from the GPU class-incremental literature): k = 1: alpha 4 / 8 / 16 / 32 -> 48.4 / 48.5 / 47.4 / 42.5 (new words 14 / 17 / 22 / 30, old 82 / 79 / 72 / 55);
  k = 2: 50.4 / 50.4 / 50.7 / 47.9. At best +0.5, a trade of old for new words again. Cosine-style normalisation by row mass makes the small-mass new rows win everything (old words 0%).
- **Max over shifts at test time** (`fewshot_words_maxshift.py`; word start at frames 4..8 and one frequency row up / down; per-class score = max instead of sum): k = 1: max 5,6,7 47.8, max 4..8 47.4, max over time + rows 47.3, vs sum 5,6,6,7 49.0 and single 48.0;
  k = 5: 50.0 / 49.3 / 49.0 vs 51.3 / 51.5. **Max is worse than the sum** (old words rise, new words fall).
- **Trace-rule detectors** (`hw/brain/trace_features.py`, `fewshot_words_trace.py`; detectors learned by tying the windows of time-shifted copies of each recording, Foldiak-style slowness learning, no labels): new words with virtual examples and LOOK AGAIN, k = 1 / 2 / 5:
  20.6 / 27.5 / 25.4 vs 22.2 / 22.0 / 26.3 (plain detectors); all ten words 51.1 / 54.0 / 55.5 vs 51.1 / 51.7 / 55.5. Noise level; no consistent gain.
Together with sections 3-7 the picture is the same every time: a new word from 1-5 recordings is mostly called an old word, every cheap correction trades old-word accuracy for new-word accuracy at roughly the same total, and the one thing the literature says works
(an embedding learned from many words) cannot be tested with the 10 words available here. See also [research note](../../../../docs/research_fewshot_gpu.md).

## 9. Why new words fail: the confusions follow word pairs, not learning order (20 Oct; SIMULATED, 3 draws, single view)

Triggered by three outside reviews (Perplexity / Gemini / GPT prompts pasted by the user): check whether the blocker is unequal treatment of old and new classes, overlapping features, or learning order (`newword_diagnosis.py`, `newword_pairwise.py`).
- **Confusion pairs (shipped: old 0-4 known, new 5-9 from k recordings).** New -> old errors go to the acoustically similar twin: with k = 1 right -> left 64%, off -> up 57%, go -> no 47%, stop -> up 46%, on -> down 40%; k = 5: right -> left 56%, on -> down 52%, go -> no 39%.
- **Swap the groups (old = words 5-9, new = 0-4).** The same pairs fail in the other direction: no -> go 78% (k = 1) and 77% (k = 5), down -> go 53%, left -> right 34-41%, up -> off 29-39%; new-word accuracy 17.6 / 22.8 (k = 1 / 5), old 86.6 / 88.2. So the errors follow the WORDS (rhyming or similar-sounding pairs), not which group was learned first.
- **Equal treatment, all ten words from scratch with the same k recordings each:** chip table 28.9 / 36.4 / 46.6% (k = 1 / 5 / 20; chance 10%), identical mean-prototype L1 readout 18.3 / 23.9 / 28.3%. With equal enrolment there is no old / new asymmetry (group accuracies are level) and still few-shot accuracy is low, so unequal treatment is NOT the blocker: the code is not sample-efficient for these words, and the shipped case (48-55% over ten words) is better only because the five old words are known well.
- **Candidate B (pair-specific discriminative counters; the votes use per-class occurrence rates, thresholds and the vote count chosen on a development set, never on test clips):** k = 1: 48.4 vs 48.5 plain (new 10.0 -> 11.8, old 86.0 -> 84.1, new -> old errors 73.8 -> 66.9%, old -> new 6.0 -> 8.3%); k = 5: 52.3 vs 51.5 (sd 0.02), new -> old 53.4%. A trade, within the draw spread.
- **Candidate D (reliable negative evidence, missing reliably-present bits):** k = 1 46.6 (new 4.5), k = 5 51.3: worse.
- **Self-training on an unlabelled pool (`newword_selftrain.py`, 100 clips per word, 2 rounds; only clips predicted as a NEW word with margin > tau are learned):** all ten words k = 1 / 2 / 5: 50.6 -> 51.3, 50.8 -> 52.4, 52.3 -> 53.7 (+0.7 to +1.6) at tau 0; new words 15.6 -> 24.6, 15.9 -> 24.9, 19.5 -> 27.6; old words 84.7 -> 77.4, 84.7 -> 79.1, 84.3 -> 79.1; pseudo-label precision only 33-47% (tau 150: 47-71% but the gain disappears). A small consistent gain of about +1 point.
- **Not applicable or already in the design:** temporal bins (the code keeps position in time and frequency), mistake-driven readout (the table is one), offline backprop embedding (outside the no-backprop rule and needs many words), augmentation (virtual examples, +2).

## 10. More words, a GPU-style baseline and a finer sound grid (20 Oct; SIMULATED, 3 draws, single view)

**More words (`fsdd_prep.py`, `fsdd_words.py`).** Extra words: the Free Spoken Digit Dataset (10 digits, 3,000 clips, 6 speakers, 8 kHz resampled to 16 kHz; fetched from raw.githubusercontent.com, the only data host this environment reaches), run through the same integer cochlea.
Shipped few-shot (old = SC 0-4, new = SC 5-9 from k = 1 / 5 recordings), all ten words / new words: detectors fitted on words 0-1 (shipped) 48.0 / 11.1 and 51.5 / 18.5; detectors fitted on FSDD + 5 SC words 47.3 / 9.6 and 51.9 / 19.0; detectors fitted on FSDD only (never heard any of the ten words) 47.1 / 9.0 and 52.8 / 22.1.
Adding the 10 digits as 10 more KNOWN classes (scenario M): 46.7 / 8.4 and 50.1 / 15.3 (worse: more old classes capture more new-word clips, 79% / 70%). **More words for detector fitting does not help; more known classes hurts.**
**GPU-style baseline (`gpu_style_fewshot.py`, floating point, backprop, diagnostic).** A small CNN trained with cross-entropy on the old words only, frozen, new words enrolled as mean-embedding prototypes (cosine): all ten / new / old: k = 1 55.1 / 25.5 / 84.0, k = 5 63.7 / 43.5 / 83.3;
pretrained on the 5 old words + the 10 digits: k = 1 53.6 / 21.0 / 85.4, k = 5 65.4 / 49.0 / 81.4. **So the failure is not only a data problem: a learned embedding beats our chip even with 5 known words (63.7 vs 51.5 at 5 recordings), and 10 more pretraining words add +5 new-word points at k = 5.**
**Unsupervised bit selection (`newword_bitselect.py`).** Keep only code bits active in >= 0.2% of the old words' clips (11,541 of 23,040): k = 1 / 5 all ten 48.2 / 53.2 (new 12.0 / 22.7); stronger pruning (>= 1%, 2%, 5%, 10%) is worse (47.3 / 52.0, 47.9 / 50.1, 46.7 / 51.0, 44.3 / 47.3).
**Finer sound-code grid (`fewshot_words_geometry.py`, spec = window h, w, stride rows, stride time, pool rows, pool time, detectors; code size 23,040 bits unless noted), k = 1 / 5, all ten / new / old:**
5,5,2,2,2,2 (shipped) 48.0 / 11.1 / 84.0 and 51.5 / 18.5 / 83.6; 5,5,1,1,4,4 50.7 / 19.2 / 81.4 and 54.1 / 25.4 / 82.2; 5,5,2,1,2,2 (46,080 bits) 49.0 / 15.0 and 54.2 / 26.2; 5,5,2,1,2,4 49.2 / 13.3 and 54.7 / 26.3;
**3,3,1,1,4,4 50.9 / 16.8 / 84.2 and 58.5 / 32.3 / 84.1** (old words unchanged). Finer time resolution and small windows help the onset-driven twin pairs; the full check of this geometry on all other tests is in the next section when finished.

## 11. Describe a new word by its match to many known words: the table-score embedding (20 Oct; SIMULATED, 3 draws, single view) - the first fix that lifts new words without lowering old words

Brain idea (relational / familiarity-profile coding): a new word is not written into the table (where it must outscore well-learned old rows) but described by the vector of table scores it produces over the KNOWN classes; new words are stored as prototypes in that score space.
Integer only: scores are the table's own sums, prototypes are sums of score vectors, the decision is a nearest prototype by L1 (adds, abs, compares); old words get K prototypes by integer competitive learning (winner = smallest L1, winner += (x - winner) >> 5).
Files: `save_word_codes.py`, `newword_tableembed.py`, `newword_tableembed2.py`, `newword_embed_hybrid.py`, `newword_embed_protos.py`, `newword_embed_protos_ema.py`. Known classes: Speech Commands words 0-4 + the 10 FSDD digits; new words 5-9 from k recordings; all ten / new / old.
- Embedding from the 5 old classes only: 27-30% (useless). From 15 known classes, 1 prototype per word, k = 1 / 5: 50.9 / 64.3 (new 17.5 / 49.5, old 83.5 / 78.7); cosine 52.0 / 63.8; same as the GPU-style CNN baseline (53.6-55.1 / 63.7-65.4). Number of known words (L1, raw scores): 7 known 50.0 / 57.5 (k = 1 / 5), 10 known 51.7 / 63.8, 15 known 51.2 / 63.2: **the more words the chip already knows, the better it learns the next one.**
- Raw integer scores work as well as centred ones; subtracting the clip's best score is worse (45-50 / 50-52).
- Old words with K prototypes (integer competitive learning), k = 1 / 2 / 5: K = 1 old 83.5 / 80.1 / 78.7, new 17.5 / 35.6 / 49.5; **K = 3 old 86.3 / 84.9 / 83.8, new 11.4 / 25.9 / 38.5, all ten 49.3 / 55.8 / 61.5**; K = 4 old 87.5 / 85.8 / 85.2, new 10.7 / 25.2 / 36.3; K = 6 old 87.9 / 86.6 / 85.9, new 9.1 / 22.2 / 33.6.
  Shipped (new rows in the table): all ten / new / old 48.0 / 11.1 / 84.0 (k = 1), 50.0 / 12.7 / 86.3 (k = 2), 51.5 / 18.5 / 83.6 (k = 5). So with K = 3 old words are the same or better, new words equal (k = 1) or about double (k = 5), all ten +1.3 / +5.8 / +10.0: **no trade-off against the shipped chip.** K = 1 gives the best total (64.3 at k = 5) but costs 5 points of old words.
- Failures on the way: a confidence gate that lets the table answer old words (new-word accuracy 3-9%: new clips are also confident), k-means prototypes with K = 16 per old word (old 88-89, new 4-22).
- Only the new-word path changes: the table, all-at-once and staged accuracy of digits, clothing and words are untouched. Not yet in the RTL; not yet combined with the finer sound grid (3,3,1,1,4,4: new words 32.3 vs 18.5 at k = 5 in the table path).

Related: [month4 index](INDEX.md), [Redesign 1 note](fewshot_imprint.md), [Research: weak spots](../../../../docs/research_weak_spots.md), [Project memory](../../../../docs/PROJECT_MEMORY.md)
