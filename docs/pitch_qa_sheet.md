---
title: SPARK Cortex pitch Q&A sheet
date: 2026-10-18
tags: [pitch, qa, cortex]
---
# Questions the judges are likely to ask, with honest answers

Every answer keeps the label (SIMULATED / ESTIMATED / MEASURED). Source of each number: [claims sheet](cortex_claims_sheet.md), [results at a glance](results_at_a_glance.md).

**1. Has it run on real hardware?** No. The design fits a Tang Nano 20K in place and route (SIMULATED) and the RTL is bit-exact with the model, but the board run is the next milestone and gives the first MEASURED numbers.

**2. Is this the first chip that learns continuously?** No. Hyperdimensional-computing accelerators and Intel Loihi 2 exist ([prior art](prior_art_cortex.md)). What is new is the combination: dreams generated from 10-bit counters (no stored examples), a night that ends by itself, no multiplier, bit-exact from raw senses to the decision. In our own test after 5 stages we are ahead of HDC on digits by 2.2 and on sound by 5.7 points (SIMULATED).

**3. Does it match a neural network?** Learning everything at once, with the slow-table option (ASIC; 5 seeds, LOOK AGAIN, SIMULATED): digits 98.3 vs 97.8, clothing 87.9 vs 87.3, words 87.2 vs 85.5 for a small MLP on the same input: level, not better. A floating-point MLP we trained on raw clothing pixels reached 88.4 and a small CNN 89.2 (words: CNN 91.4). Without the slow table the network is ahead on clothing (84.8 vs 87.3). The chip's advantage is learning in stages: digits 95.8, clothing 78.3 (80.0 with the finer-grid option), words 82.9, vs a network that forgets (19.5 / 20.0 / 15.9).

**3b. What limited the scores, and what did you do about it?** A floating-point classifier trained on the chip's own code reaches 87.9% on clothing and 98.3% on digits, so the senses are not the limit; the one-pass 5-bit readout is. A slow second table that follows the fast one (shifts and adds, bit-exact in RTL, ASIC option, +1.6x table memory) gives clothing 83.4 to 86.9, words 83.1 to 85.7, digits 97.0 to 97.6 (single view). A finer detector grid for images adds clothing 88.0 and digits 98.3 all at once but makes staged digits worse (93.2), so it is an option.

**4. Does it really never forget?** No, do not say that. A new condition of known classes (rotated digits) dropped upright digits from 95 to 45%; a frozen dream memory keeps 85% and is an ASIC build option in the RTL (SIMULATED).

**5. Where did it fail, and what did you try?** Staged learning is limited by dream fidelity (the last-stage classes absorb older ones); cheap fixes (more daydreams, margins, structured dreams, bias rules) failed; only prototype dreams help (+2 on clothing for 4x dream memory). Spoken words from 1 to 5 recordings stay weak (12 to 29% on the new words). Also rejected: a second sensory layer, expansion coding, onset channels, tempo and pitch normalisation, wider-in-time sound detectors (about 2 points worse), a shared prototype pool (no memory saving), table rebuilds and merge variants. Kept: IMPRINT + short sleep, word alignment, LOOK AGAIN, margin 32. Failures are in the [journal](journal.md).

**6. What does it cost?** Images: 84 KB memory. Sound: 422 KB (needs PSRAM or an ASIC). The Tang Nano uses 89% logic, all 46 block RAMs and 0 multipliers (SIMULATED place and route). SKY130: logic under 1 mm2, 18.8 mm2 with open SRAM macros (ESTIMATED).

**7. How much energy does it save?** About 74x per decision counting only the operations needed (9.4 nJ vs 696 nJ against an 8-bit network, ESTIMATED). The SKY130 layout estimate is 0.18 to 0.26 uJ per decision, 20 to 28x above the operation count. Say "per operation needed", not "per chip".

**8. Why no multiplier or backprop?** The brain principle we committed to. Learning is counting into a 5-bit table and 10-bit counters; dreams are rejection sampling from counters; the sense layer is XNOR plus popcount and winner-take-all.

**9. What are dreams, in one sentence?** While idle, the chip draws pretend examples of old classes from its counters and learns them again, so new learning does not overwrite old knowledge, and it stops by itself when the table stops being surprised.

**10. How does one chip give knowledge to another?** Because memory is counts: merge two chips by adding counters (91.4% on all ten digits after one night in the board-demo emulator), or hand over one memory and keep learning (95.6 / 82.7 / 71.6, SIMULATED).

**11. Why does this matter (scope)?** Less retraining means less energy, less heat and less discarded hardware; weight transfer without a server; learning in the field. It is a small continual learner for sensors (images, sound), not a language model, and it does not replace GPUs.

**12. What is the layout status?** SKY130 open-source flow, detailed routing at 1 remaining violation at a memory-macro edge (from 174,309 on the first pass), ESTIMATED, no sign-off, no fabrication planned yet.

**13. What will you do with more time or money?** First the board run (MEASURED numbers), then learned word features and higher-fidelity dreams for clothing, then write-up and demo video; horizon 6 to 8 months, then shrink the design and look for investors.

**14. Is the data realistic?** Standard digit and clothing image sets and a small spoken-word set (10 words). Results on larger vocabularies or real noise are not tested; say so.

Related: [Pitch script](pitch_script_cortex.md), [Claims sheet](cortex_claims_sheet.md), [Results at a glance](results_at_a_glance.md), [Project memory](PROJECT_MEMORY.md)
