# Project scope (agreed with the founder)

**The idea:** a brain-inspired chip. We take how brains compute and move memory, build those principles into SPARK, and prove with
measured numbers that the concept works. Not "replace the GPU" and not "a faster LLM decoder"; those are things we check against,
not what we are building.

**Constraints:** short horizon (weeks, not years). No fabrication until the design is small and the concept is proven; not at 130 nm now.
Every claim labelled MEASURED / SIMULATED / ESTIMATED / PROJECTED.

## In scope (each ties a brain principle to a SPARK measurement)

| Brain principle | SPARK experiment |
|---|---|
| Sparse, event-driven activity | events/cycles vs accuracy curve; firing-rate target |
| Compute where the weights live | multiply-free (ternary) weights; smaller weights and smaller chip |
| Fast store + slow store (hippocampus / cortex) | recall memory + network; hysteresis counters (synapse-like); replay consolidation |
| Predictive coding (only surprises travel) | draft = prediction, big model = error signal; confidence |
| Only relevant neurons run | activation sparsity of real models; what predicts it |
| Shrink before fabricating | hidden size vs accuracy; weight bits vs accuracy |

## Out of scope (parked, kept only as a baseline check an investor will ask for)

Copy/suffix-matching engines, tree-width sweeps of software drafting, wall-clock timing of prompt-lookup decoding,
and any "AGI / System 2 substrate" claim.
