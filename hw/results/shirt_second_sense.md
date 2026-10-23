---
title: Second sense for Shirt against T-shirt (24 Oct 2026)
tags: [l, clothing, two-sense, results]
---

# Does a second sense (an ear hearing the garment's name) resolve the Shirt / T-shirt confusion? (SIMULATED, one seed)

> **CORRECTION (24 Oct 2026, user's objection, accepted): this is NOT a classification gain.** A spoken name of the garment *is the label*. Giving the model a noisy label at test time and finding that it answers better is an oracle-label experiment: it shows the table adds two witnesses correctly, nothing about telling shirts from T-shirts by looking. A deployed model must not need the label at test time, so **the honest Shirt/T-shirt picture-only result stands (Shirt recall 63 to 74%, CNN ruler 79.4%)** and the numbers below must not be quoted as an accuracy improvement. A name at *training* time (a teacher saying the word while the picture is seen) is legitimate and is how L already learns; only the test-time use is invalid. A valid second sense must be independent evidence about the object that is not its name: colour, finer resolution, touch or weight, size, context. None of these exist in the grey 28 x 28 data set, so no fair test is possible on it. The same caveat applies to any earlier two-sense gain where the sound was the spoken label of the object (see the memory file); those results show cross-sense learning and repair, not better recognition without the label.

`hw/brain/experiments/month5/shirt_second_sense.py`, log `shirt_second_sense.log`. Same integer slow-table model and stride-1 picture code as before, single view, all at once, trained and tested with a sound code appended to the picture code (1,024 bits, 64 active, one fixed sparse pattern per spoken name) in the same table. The ear is **a model, not real audio**: it hears the right name with probability `acc` and otherwise a random other name, **independently of the picture**. The ear is present at training and at test.

| Setting | Overall | Shirt recall | T-shirt recall | Shirt called T-shirt | T-shirt called Shirt (per 1,000) |
|---|---|---|---|---|---|
| Picture only | 88.85 | 63.8 | 87.8 | 147 | 59 |
| Picture + ear right 60% | 92.52 | 78.8 | 89.2 | 66 | 48 |
| Picture + ear right 74% | 94.49 | 86.8 | 92.2 | 37 | 35 |
| Picture + ear right 90% | 97.24 | 93.8 | 95.7 | 15 | 15 |
| (ear alone at 60 / 74 / 90%) | 59.2 / 73.2 / 89.9 | 62.9 / 76.4 / 90.8 | 56.7 / 72.6 / 90.7 | | |

**Reading.**
- Two independent, individually imperfect witnesses beat either alone: an ear that is right only 74% of the time (about the accuracy earlier measured for unfamiliar speakers) lifts Shirt recall from 63.8 to 86.8% and halves both confusions. That is better than the CNN ruler on Shirt (79.4%) with no backprop and no extra table machinery.
- At 60% ear accuracy the combination is still +3.7 overall, +15 points on Shirt.
- The mechanism is the one the project already uses (two senses summed in one table): errors of the two senses are unrelated, so the sum is right more often.

**What this does NOT show (read before quoting).**
1. The ear is simulated with errors independent of the picture. A real ear confuses similar-sounding words; "shirt" and "T-shirt" differ by a syllable so they should be well separated acoustically, but this has not been tested with real speech of these words (no recordings of clothing names exist in this repository; the real audio work used digits and Speech Commands words).
2. It needs the name to be spoken or available at test time. If no name is available, the picture-only limit stands (Shirt about 64 to 74%).
3. One seed; the sound code adds 1,024 bits here (the earlier full sound front end added 23,040 bits).
4. Not a replacement for the picture: it is a second source, which is also the answer to "the model should not stay confused": ask the second sense when the picture's margin is small.

**Next step.** Record or synthesise real spoken clothing names, run them through the existing cochlea model, and repeat; and test the "ask only when unsure" rule (use the ear only when the picture's top-two margin is below a threshold).

Related: [Results index](INDEX.md), [Specialist for Shirt/T-shirt](shirt_specialist.md), [Where L loses on clothing](clothing_confusion.md), [Journal](../../docs/journal.md), [Project memory](../../docs/PROJECT_MEMORY.md)
