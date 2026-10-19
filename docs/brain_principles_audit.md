# Brain-principles audit of SPARK Cortex (21 Oct 2026)

User rule (21 Oct): follow the principles of the brain strictly in every process. This note lists the test every process must pass,
audits each process of the current design against it, and sets the order of fixes. Fixes are PROJECTED until measured.

## The test (a process passes only if all hold)

1. **Local rule.** A synapse changes from what its own two neurons did, plus at most one broadcast signal (surprise / reward). No global optimiser, no gradient.
2. **No outside conductor.** Learning, sleeping, and "a new class has arrived" come from signals inside the chip, not from a host schedule or a told class list.
3. **Few labels.** A teacher is a sparse reward, not a tag on every example. Unlabelled experience must also change the chip.
4. **One pass, no stored data.** Memory is the synapses. No dataset, no stored examples, no replay of raw inputs.
5. **Sensing is innate or learned locally.** Fixed, evolved-style front ends (cochlea, retina) are fine; hand-made segmenters and offline fitting are not.
6. **Cheap and sparse.** Events, compare, count, add, shift, XOR. No multiply, no float.

## Audit

| Process | Passes? | Why / fix (PROJECTED) |
|---|---|---|
| Receptor thresholds, retina centre-surround | yes | fixed innate front end |
| Cochlea resonators + noise floor | yes | fixed innate, adaptation is brain-like |
| **Word alignment** (centre the word in the window) | **no** (test 5) | hand-made segmenter; fix: energy-onset trigger (adaptation + compare), the ear's own onset response |
| **Detectors fitted offline on a PC** | **no** (test 5) | the on-chip learning (`ENC_LEARN`) already exists in RTL, bit-exact (94.5 / 80.0 vs 95.0 / 79.2); make it the default path, keep plasticity running |
| Detector competition (winner by XNOR + count) | yes | competitive Hebbian |
| Fast table, written only on surprise | yes (rule), **no** (test 3) | the surprise rule is local; but "wrong" needs a label on every example |
| **Label on every example** | **no** (test 3) | fix: label only a fraction; at night the chip tags its own confident winners (self-labelling) and writes only on surprise; test 10 % labels vs full labels |
| **Host schedule: stages, "day", "night"** | **no** (test 2) | fix: sleep pressure, an internal counter of surprises and time that starts sleep; the night already ends itself (`night_stop`), so only the start is outside |
| **Host tells the chip which classes are new** | **no** (test 2) | fix: novelty from the chip's own scores; a plain novelty gate only traded old for new (recorded 19 Oct), so it needs the sleep step to settle it |
| Dream memory (counts, halving) | yes | synaptic scaling |
| Dreams with independent bits | partial (test 4 holds, fidelity weak) | memory is counts only (good); fidelity is the known limit; prototype dreams help, cost 4x dream memory |
| Slow table (consolidation) | yes | cortical consolidation, shift/add only |
| Embedding path | yes | relational coding of new things against known ones |
| Context memory (sim only) | yes | hippocampal context |
| Merge two chips by adding tables | not a brain claim | brains cannot merge; keep as an engineering feature and say so |
| Noisy dreams (script written, not run) | plausible | imperfect replay is brain-like; must not lower old words |
| Benchmarks, scripted stages | n/a | the way we test, not the chip |

## Order of work

1. Few-label learning with self-labelling at night (biggest gap, tests 2 and 3).
2. Onset-triggered words (test 5, removes the hand-made step).
3. Sleep pressure and novelty from inside (test 2); needs care, the plain novelty gate failed.
4. On-chip detector learning as the default (test 5), already in RTL.
5. Noisy dreams, only if old words stay level.

Each is written to `hw/brain/experiments/`, logged in the journal with its label, and reported whether it wins or fails.
Before the 23 Oct event none of these can be finished and measured properly: the deck and Q&A should say plainly which steps are engineered (see the table).

Related: [Project memory](PROJECT_MEMORY.md), [Journal](journal.md), [SPARK Cortex redesign](cortex_redesign.md), [Docs index](INDEX.md)
