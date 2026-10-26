---
title: Sequence memory - burst allocation of longer contexts
tags: [spark, results, thinking, sequence]
---

# Sequence memory: burst allocation of longer contexts (26 Oct 2026)

SIMULATED, one corpus. Part 2 of the thinking plan, first test of our own design (the research notes were references, not predictions). Script `hw/brain/experiments/month5/seq_order_test.py`, log `seq_order_test.log`. A counting sequence model carries one integer of state: the longest context order matched so far. It stores a context only after an error: when the longest matching context predicts the wrong byte, the next longer context is allocated. Counters only, no multiply. Compared online (predict, then update, one pass) on 700,000 bytes of this repo's markdown notes, scored on the second half, against (a) a fixed window of the last k bytes and (b) a full backoff model that stores every context up to order k. Memory is counted in stored contexts (entries), not bytes.

| model | next-byte accuracy | stored contexts |
|---|---|---|
| fixed window, best (order 4) | 57.0 | 74,489 |
| fixed window, order 6 / order 8 | 52.1 / 43.6 | 240,266 / 389,044 |
| full backoff, order 4 / 6 / 8 | 58.7 / 61.9 / 62.9 | 101,611 / 495,064 / 1,203,710 |
| burst allocation, max order 4 | 58.0 | 62,411 |
| burst allocation, max order 6 | 60.4 | 170,564 |
| burst allocation, max order 8 | 60.9 | 237,738 |
| burst allocation, max order 12 | 61.2 | 281,407 |

- **Better accuracy per stored context than a fixed window** (58.0 with 62 thousand contexts against 57.0 with 74 thousand at order 4, and far better than a longer window, which gets worse because it never backs off), and **about 4 to 5 times fewer contexts than full backoff for 1.7 to 2 points less** (60.9 against 62.9 at order 8, 238 thousand against 1.2 million).
- The state is one integer (the matched order), carried from byte to byte, and the allocation rule is the same "write only when wrong" as the rest of L.
- Caveats: one small, repetitive corpus (our own notes, which repeat phrases heavily); contexts counted, not bytes; no hashing or capacity limit applied; no test of a carried hypothesis (this is a memory-efficiency test of the sequence core, not of thinking steps). The synthetic hidden-state task and joining the core to the recogniser are not done.

Related: [Counting language model, first test](counting_lm.md), [Thinking synthesis](../../docs/research/thinking_synthesis.md), [Results index](INDEX.md)
