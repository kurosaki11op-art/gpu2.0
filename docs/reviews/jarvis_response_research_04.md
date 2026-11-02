---
title: Jarvis response to research 04 - accepted; the founder builds the software layer anyway, so CUDA is researched first (2 Nov 2026)
tags: [spark, review, response, software-for-hardware-makers, cuda]
---

# Response to research 04 (2 Nov 2026)

Reviewed: [research 04 summary](research_04_summary.md) and its notes (merged from `vision/research-4`). I did not re-read the primary pages.

## Accepted

- **Software for chip makers:** chip makers pay for the software layer (four large deals in 13 months bought whole teams), but I should not have suggested that small outside teams are paid for it; no contract, price list or funded firm was found. I withdraw "a service you could sell soon" as a claim; it is an untested hypothesis with a kill test (ten conversations with software leads at chip companies; at least two scoped paid pilots or written access within six weeks).
- **Paid categories:** the ones with money need GPUs and capital; the ones a two-person team could build (cost visibility, measurement) have the weakest evidence of payment; orchestration and sharing are covered by a free scheduler that Nvidia now owns; I have no independent product evidence for failure recovery.
- **Jevons:** weak to moderate evidence, mostly second-hand; one first-party signal (a vendor raising its flagship tier price) points the other way. I will not use Jevons as an argument either way.
- **India:** the portal is usable (requests under 5,000 GPU-hours auto-approved, subsidy up to 40%, an H100 hour listed at 153 rupees before subsidy); blog claims of 65 rupees do not match the portal. The founder can use it to get compute for tests; the official GPU count is unverified.
- **My recollections** (an orchestration acquisition in 2024, the scale of an Indian programme, funding sizes) were unverified and are superseded by Vision's findings where they overlap.

## Decision recorded

The founder will **build the software layer regardless** of whether outsiders pay for it, as the base for a later chip; Vision is asked to research CUDA first ([task 05](../vision_research_task_05.md)). My honest reservations, on record: there is no evidence yet of a buyer, so the work is a bet on the founder's own path (learning, credibility, a possible later chip), and it should carry kill criteria: a defined scope, a pre-set bar for what it must run and how fast, and a date.

Related: [Research 04 summary](research_04_summary.md), [Research task 05](../vision_research_task_05.md), [Reviews index](README.md)
