---
title: Thinking research synthesis and build order
tags: [spark, research, plan]
---

# Thinking research synthesis and build order (26 Oct 2026)

> How to read this note (founder's rule, 26 Oct 2026): the papers are references to learn from, not evidence about our own result. A method failing in a paper does not mean it fails here; their conditions, data and rules differ from ours. Every item below is an open question that our own experiments decide, and we record the outcome whichever way it goes.

Five research agents each read papers for one of the five missing parts of "thinking" and proposed methods under our rules (matrix-free, multiply-free, no backprop in the chip design). Notes: [1 imagination](papers_notes/thinking_research_1_imagination.md), [2 working memory](papers_notes/thinking_research_2_working_memory.md), [3 hypothesis loop](papers_notes/thinking_research_3_hypothesis_loop.md), [4 goals](papers_notes/thinking_research_4_goals.md), [5 composition](papers_notes/thinking_research_5_composition.md).

## How much was really read

Each note has a table of what was read in full. After a second pass (the first pass was too shallow and was sent back), about 9 to 14 papers per topic were read through the whole main text; the rest are marked partial. Unreachable through the proxy (not bypassed): wake-sleep, the RBM originals, Olshausen-Field, CN2/RIPPER, query-by-committee, Orseau-Armstrong interruptibility, quantilizers, Plate, Kanerva 2009, Smolensky 1990. Figures were not inspected for several papers (PDF reader limit). All numbers below are as reported by the papers, not ours.

## What the papers say, per part

| part | main finding that changes our plan | top proposed method (all UNTESTED) |
|---|---|---|
| 1 imagination | Our dreams were one product distribution; the missing level is a mixture. Sum-product networks learn by counting winning children. Generative replay works better when dreams are labelled with the old model's soft score vector than with hard labels (reported 91.8 against 19.9 for fine-tuning, split MNIST). Forward-Forward draws negatives from the wrong classes in proportion to the model's own scores. | Counted sub-prototypes per class (a stored code plus mask per slot, K up to 32) with dreams kept only near the old table's boundary and labelled by its scores; about 62 KB at K=8 (ESTIMATED). |
| 2 working memory | A recurrent Tsetlin paper (2026) found clause feedback did not beat a window-only control: every design must beat a window-only baseline. Infini-gram's matched order grows by at most 1 per token and works as a one-integer carried state; its count indexes merge by addition. | Hashed multi-order counting core with a longest-matched-order state and burst allocation on error, tested against window-only and first-order controls; about 2 MB (ESTIMATED). |
| 3 hypothesis loop | Popper's logic fits clauses (fires wrongly: too general, add literals; never fires: too specific, drop literals). A counts-only lower-bound test (SSDPS) is a trust test for small data. Tsetlin Type II feedback is already a built-in "why not"; its partner class is random, so choosing the partner is a new cheap lever. No paper offers a damage budget; that part is ours. | Contrast counter proposes 2 to 4 literal clauses, Popper-style refinement, lower-bound acceptance on a separate set with limits on breaks per class and probe flips. Target: Shirt recall 0.638 to at least 0.67 with overall accuracy down by at most 0.2; risk: counted vetoes were weak, gain may cap at 1 to 2 points. |
| 4 goals | Set-points must be read-only (a learner that learned preferences from its own behaviour drifted). Uniform sampling is a strong baseline; learning-progress choice only roughly equals a hand-made curriculum, so success is parity. Safety: a stop must cost the agent nothing; penalise loss of other abilities with an absolute measure and a no-op baseline. | Progress-ranked rehearsal: per-class doubt progress on an unlabeled buffer, Thompson-style choice with a fixed 20% uniform share, a night that ends when progress is near zero, a decision log. |
| 5 composition | Composition has two kinds: object sets generalise (97% on 3 to 4 objects after training on 1 to 2), held-out attribute combinations do not (0% with multiplicative binding, 0 to 72% with additive key-value bundling). Binding is cheap in sparse form (index addition mod block size, XOR). Resonator capacity falls off sharply above about N squared. | Cheapest first: XNOR relation clauses (same/different) on unseen classes; then one counting table per attribute plus a small signature clean-up, leave-one-class-out test, pass at 40% in 5-way (chance 20%). |

## Proposed build order

1. **Imagination, counted mixture with soft labels (part 1).** It attacks the open weakness of the continual-learning claim (late classes never see their look-alikes). Test inside the staged rehearsal pipeline against the 83 to 84 result with 20 stored images.
2. **Hypothesis loop (part 3).** Directly measurable on the Shirt confusion and reuses the controller; honest risk of a 1 to 2 point cap.
3. **Progress-ranked rehearsal (part 4).** A small extension of the controller; success is parity with fewer steps and no human-set schedule; add the read-only set-point rule and a decision log from the start.
4. **XNOR relation clauses, then attribute tables (part 5).** Cheap first test; tells us early whether composition is reachable at all under our rules.
5. **Multi-order counting core with a carried state (part 2).** Largest build; must beat the window-only control or it is dropped.

Parts 1, 3 and 4 raise accuracy or autonomy of what already runs; parts 2 and 5 add capabilities we do not have (sequence state, composition) and are the least explored. None of this is tested; each step gets a success criterion before it is run and its failure will be recorded as clearly as a win.

Related: [Research papers notes](papers_notes/INDEX.md), [Project memory](../PROJECT_MEMORY.md), [Docs index](../INDEX.md), [Lessons from failures](../lessons_from_failures_25oct.md)
