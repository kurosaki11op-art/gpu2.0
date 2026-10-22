---
title: Research - GPU few-shot and class-incremental tricks, integer analogues (19 Oct 2026)
date: 2026-10-19
tags: [research, fewshot, class-incremental]
---
# Research: GPU few-shot / class-incremental tricks and integer analogues for L Cortex
Caveat: search snippets only; arxiv.org fetch failed (DNS). Items marked (memory) are from my background knowledge, not verified this session.

## Sources
- Weight Aligning (Zhao et al. 2020) https://arxiv.org/pdf/1911.07053 : post-hoc, rescales new-class FC weights so their mean norm equals old-class mean norm (gamma = mean|w_old| / mean|w_new|); no extra params/val set.
- CIL survey (Masana) https://arxiv.org/pdf/2010.15277 : recency bias = larger classifier norm AND bias for newest classes; iCaRL's nearest-mean avoids it.
- BiC https://openaccess.thecvf.com/content_CVPR_2019/papers/Wu_Large_Scale_Incremental_Learning_CVPR_2019_paper.pdf : 2-parameter linear correction on new-class logits only, fitted on small validation set.
- LUCIR cosine normalisation (secondary description via survey above); logit adjustment (Menon) = add tau*log(prior) offset (secondary only).
- PASS https://openaccess.thecvf.com/content/CVPR2021/papers/Zhu_Prototype_Augmentation_and_Self-Supervision_for_Incremental_Learning_CVPR_2021_paper.pdf : one prototype per old class + Gaussian noise; SCFR (FSCIL) same idea. YONO critique https://ar5iv.labs.arxiv.org/html/2305.16143 : noise distorts structure.
- Brain-inspired replay https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7426273/ : replay hidden (feature) representations, Gaussian-mixture latent, class-gated; no stored data; I did not see tables.
- Few-shot KWS: https://arxiv.org/pdf/2007.14463 (protonets), Mazumder et al. 2021 https://arxiv.org/abs/2104.01454 (embedding pretrained on many words, 5 shots -> F1 0.75 on 180 new keywords, 9 languages; snippet-level).
- FSCIL: frozen base-trained extractor + prototypes as classifier weights is the standard baseline; CEC/FACT/NC-FSCIL numbers differ by backbone (https://arxiv.org/pdf/2302.03004, https://arxiv.org/pdf/2312.05229 training-free prototype calibration, TEEN: new prototype is blended with similar old prototypes (memory)).
- HDC: Berkeley EECS-2022-118 https://digitalassets.lib.berkeley.edu/techreports/ucb/incoming/EECS-2022-118.pdf (HDC for always-on audio, general); no HDC few-shot KWS paper found.
- SNN KWS survey https://arxiv.org/pdf/2506.01737 : few-shot and class-incremental SNN KWS listed as OPEN problems. Loihi KWS (Blouw) https://arxiv.org/pdf/1812.01739 trained offline.

## A. Candidate mechanisms (ranked gain x ease)
1. Row-mass alignment (Weight Aligning). Every ~N updates (or at IMPRINT time) compute per-class L1 mass M_c = sum |w_c|. Target M_ref = mean of old classes (via sum + shift, or median-of-two). New row: shift right/left by round(log2(M_ref/M_c)) (power-of-2 gamma, no multiplier). Directly targets 69% new->old confusion IF new rows are too weak, and the staged recency problem if new rows are too strong. Cheap; note direction: for our failure the new words lose, so it is the *opposite* of recency; check measured L1 mass first.
2. Per-class bias learned from dreams (BiC/logit adjustment analogue). Bias b_c integer, added to class score. Run dream replay for ALL classes at equal count; any class winning more than its share of dreams gets b-=1, loser b+=1 (homeostatic counter). Equalises predicted-class frequency on dreams without data. Also logit adjustment: b_c = -(counter-derived log2 prior) via the leading-one position of the 10-bit on-counter (priority encoder = log2, no multiply).
3. Cosine classifier -> normalise by count of active input bits: score_c = sum w over active bits >> k_c with k_c from active-bit count / row mass. Equivalent to 1 but per-query; also gives scale invariance for clips with different numbers of active bits (a likely issue for short/long words). Ease high.
4. Max-over-shift matching at test time (not GPU 'cosine' but standard for time/speed invariance): score = max over row offsets -2..+2 and frame slack of table score; train with joint shift augmentation (Povey 2015 speed+spectral warp). Integer: 5-15 table lookups + compare tree. Likely the largest gain specifically for 1-5-shot new words since it replaces the missing pretrained invariance. Already in research_weak_spots.md.
5. Prototype calibration with old-class neighbours (TEEN-like, memory): new-class row initialised as its own few-shot counts plus a shift-weighted copy of the most-similar old class row (WTA over overlap counts). Gives a prior in the 'embedding of old words' spirit; risk: pulls new word toward the old word it is confused with, making confusion worse. Medium gain, medium ease; test with 1/4 weight.
6. Feature-level dreams instead of bit-level (BI-R analogue): draw dreams at the detector-winner level (which detector fires, k-of-n) rather than per input bit; co-occurrence is carried by the winner identity. Group-structured dreams already failed, so rank low unless detector-level (sensory layer) rather than group-level.
7. k prototypes per class chosen by WTA, dream picks a prototype then draws bits (PASS = 1 prototype + noise; YONO says noise destroys structure, so prefer k real prototypes). Cost k x counters. Medium-high gain for staged clothing; the 'multi-prototype' idea was in the existing note.
8. Dream-time margin/class-balanced replay: replay old-class dreams and new real data at ratio 1:1 per class (class-balanced fine-tune as in the survey's balanced finetuning, memory). Integer; low cost; mostly fixes recency.

## B. Exemplar-free CIL
- Prototype replay with Gaussian noise (PASS): works on a good frozen feature extractor; our analogue is the per-bit counter dream (independent Bernoulli noise around a mean) -- same limitation, which YONO calls out.
- Feature replay beats pixel replay (van de Ven 2020): replay at the highest feature layer; for us = detector-output codes, not raw pixels.
- Deep inversion, EWC, null-space projection: need gradients / matrices / Fisher; NOT implementable. An EWC-like integer analogue = per-weight importance counter that slows updates (shift larger) on weights rarely changed or heavily used; unproven here.
- Recency fixes: weight/bias alignment (WA, BiC), cosine normalisation (LUCIR), nearest-mean (iCaRL), logit adjustment, balanced replay. All map to items 1-3, 8 above.

## C. Hebbian/unsupervised few-shot audio
- Found nothing citing a direct Hebbian/HDC few-shot-KWS result with numbers. Honest finding: SNN KWS survey says few-shot/class-incremental is open; Loihi KWS was offline-trained; HDC work is general. Do not expect a drop-in recipe.
- Standard invariance sources (memory + existing note): pretrained embeddings on many words; speed+spectral warp augmentation; test-time max over shifts / banded DTW; temporal pooling and slow-feature learning (memory, not verified this session). The closest brain-like, integer option is item 4 plus a pooling (OR over 2-3 adjacent frames) of detector outputs before the table.

## Takeaway
Cheapest to try first: (4) shift-max match, (1)+(3) normalisation by shifts, (2) dream-balanced biases. Measure row L1 mass and active-bit counts per class before trusting 1/3 -- I have no evidence which direction the bias goes for new words.

## What we tested from this list (19 Oct, SIMULATED)

- Weight aligning / cosine normalisation / mass scaling at decision time (staged clothing: 78.4 plain -> 75.9 cosine, 74.0 mass-align, 78.1 mass^0.25; staged digits 94.8 -> 93.5 cosine, 95.4 mass-align): no gain or mixed; our new classes have the SMALLER row mass, the opposite of the GPU case. See [staged cosine log](../hw/brain/experiments/month4/staged_cosine.py).
- Per-class bias from dreams (+0.9) and logit adjustment by class size on new words: see [multi-prototype note](../hw/brain/experiments/month4/multiproto_dreams.md) and the calibration test.
- Max-over-shift matching for new words: see the journal entry of 19 Oct.

Related: [Weak spots research](research_weak_spots.md), [Few-shot research](research_fewshot_class_incremental.md), [Project memory](PROJECT_MEMORY.md)
