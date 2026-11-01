---
title: Research 02 summary - which GPU and CUDA weaknesses are real, which incumbents have closed, and a ranked shortlist (1 Nov 2026)
tags: [spark, review, research, weaknesses, shortlist, corrections]
---

# Research 02 summary (1 Nov 2026)

Assignment: [research task 02](../vision_research_task_02.md). Topic notes: [hardware](research_02_hardware.md), [incumbent fixes](research_02_fixes.md), [CUDA, licence and debate](research_02_cuda.md), [buyers and startups](research_02_buyers.md), [power, heat, water](research_02_power.md). I did the work independently and read Jarvis's [first pass](../restart_2_weakness_study.md) only after finishing the notes.

## The answer in brief

1. **The best-evidenced GPU weakness is not launch overhead; it is that decode uses almost none of the compute.** On a fast GPU, matrix kernels are busy about 9% of the time and use 2% to 12% of their matrix fragments at batch 1 to 8; memory is about 64% busy (arXiv 2609.12923, MEASURED, one GPU). Attention stays memory-bound at every batch size (arXiv 2504.16112, an A100 profile by a memory maker).
2. **Launch overhead is real but mostly handled.** CUDA graphs cut H100 batch-1 step time by 20.6% (1.259x), and the serving engines capture them by default. Even so, the H100 sits near 39% of its weights-only bandwidth floor at batch 1 (DERIVED). The remaining 61% is unexplained by the one paper that measured it.
3. **The CUDA licence is narrower in words than the headlines.** Item 8 forbids reverse engineering *outputs* in order to translate them to other platforms; it does not say "translation layer". No regulator action on CUDA could be confirmed.
4. **Complaints visible in public trackers are about deployment friction** (driver and CUDA mismatches, memory sizing), not speed.
5. **Buyer-need evidence is weak and mixed:** price spreads of 8.9x between providers, rising contract prices, and also reports of 5% average utilisation. No method I would trust.
6. **Startup outcomes point to financing and customer concentration, not provable software failure.** The route that paid (Groq) was a licence and team deal with the incumbent.
7. **Power is a delivery problem** (grid queues, transformers), concentrated in large racks. Half of a prompt's energy is outside the accelerator.

## Weakness table

Columns: evidence with label; who suffers; what incumbents already do; what remains; copy-resistance for a small team; cheapest kill experiment. "Bar" values are proposals to be fixed by the founder and Jarvis **before** any run.

| # | weakness | evidence | who suffers | incumbents already | remains | can a small team show a fix incumbents cannot copy quickly? | cheapest kill experiment and bar |
|---|---|---|---|---|---|---|---|
| A | Decode leaves compute idle; matrix work 2% to 12% fragment fill; attention memory-bound at any batch | MEASURED, preprints 2609.12923 and 2504.16112 (second has a memory-maker's interest) | Everyone serving low-latency decode | Batching, disaggregation, speculative decoding (2x to 3x at batch 1 to 3, gone near batch 32) | Most of the idle compute at small batch | Only with a different machine; incumbents could add decode-specific units (and Nvidia has bought a decode design) | A cycle-level model of the tile on a real layer showing at least 60% matrix-unit utilisation at batch 1 on a 7B-class layer, including memory stalls, against the same layer's measured H100 kernels |
| B | Batch-1 decode on fast GPUs reaches 31% to 39% of the weights-only bandwidth floor even with graphs | MEASURED, one preprint, plain PyTorch, one author | Low-latency users on the newest GPUs | CUDA graphs, compile, kernel libraries | About 61% of the floor, cause unknown | **Not shown yet.** A better engine on the same GPU would erase it | Run the same model with graphs plus the best available engine on the founder's own GPUs; kill if it reaches at least 70% of the floor (5 to 10 hours of work) |
| C | Reliability: one unexpected stop per about 3.1 h at 16,000 GPUs, 78% hardware | PUBLISHED, one operator, a training run | Large training users | Checkpointing, fast restart (90% effective time) | Inference-fleet rates are UNKNOWN | **No**; this is a system-software problem for large operators | Not worth an experiment for this team |
| D | Deployment friction: driver and CUDA-version mismatches, memory sizing | Issue trackers and guides [S] | Small teams and enterprises | Forward-compatibility packages, containers | Recurring | Software-only; open projects already attack it | Count the top 50 recent issues of one engine by cause (a day); kill if under 30% are driver or version problems |
| E | Power delivery for racks of 100+ kW; half of a prompt's energy is host, idle and overhead | MEASURED (Google split), THIRD-PARTY (grid queues) | Operators without grid access | Liquid cooling, bigger sites | Small-site and air-cooled gap; demand UNKNOWN | Possible for a small low-power card; Tenstorrent and others already sell near it | Ten buyer conversations; kill if fewer than two name a site-power limit as the reason they have not deployed |
| F | Quality loss by number format is poorly reported | THIRD-PARTY single write-up, [S] | Everyone choosing 4-bit | Vendors report averages | Per-model, per-size, paired-interval tables | **Yes, anyone can do it; copy-resistance zero** | Measure INT4 and FP8 loss on three model sizes on owned GPUs; pre-register 1 point as the pass line |
| G | Price opacity: 8.9x spread across providers; list-to-deal gap 7.5x on one cloud chip | THIRD-PARTY trackers | Small buyers | Marketplaces and benchmarks | Real cost per token at a given speed | Yes, as measurement; low moat | See wedge 1 in [Research 01](research_01_summary.md) |

## Ranked shortlist: weaknesses worth attacking

1. **A (decode leaves compute idle), as a simulation-first test.** It is the best-evidenced, it is what the project's tile is designed for, and it can be tested in the simulator before any money. **Caveat:** Nvidia has announced a dedicated decode part (see [Research 01](research_01_summary.md); shipping status unclear), so the weakness is known and being addressed; the question is only whether a small team can show a clear gain on a layer. **Bar:** utilisation as in the table, and a stall-inclusive cycle model, not peak.
2. **B (batch-1 gap on fast GPUs), as a one-day check before anything else.** It costs almost nothing and decides whether A's gap at batch 1 is real or a software artefact. If a good engine closes it, drop the "launch-bound" story entirely.
3. **F (format quality tables)** and **G (cost and energy measurement)** as the cheapest, copyable, credibility-building work. Not a business moat.
4. **E (small-site, low-power)** only after buyer conversations.

**Not worth attacking:** C (reliability), D (deployment friction, a software game with many open projects).

## Weaknesses that look real but are closed or mostly closed

- **Kernel launch overhead in decode:** graphs are on by default in the major engines; measured headroom beyond that is not shown (arXiv 2605.30571).
- **Fusion and compile:** integrated by default in one major engine, effect unmeasured here; do not claim it as an open gap.
- **Training-run interruptions:** handled well enough that Meta reports more than 90% effective time.
- **Low-bit weights:** the choice of kernel matters more than the bit width (3.4x between kernels), so "4-bit helps" is not a hardware claim.

## Corrections to Jarvis's first pass

| first-pass statement | my finding |
|---|---|
| Launch overhead "becomes the bottleneck on fast GPUs" and matches the founder's 1.0 to 1.5 ms per layer | The paper's own figure is a 20.6% step-time effect on H100 at batch 1 and 2.8% on L4, with graphs on by default in the engines. **The founder's per-layer measurements need checking for whether graphs were used;** if they were not, the match to a launch-bound explanation is not established. I did not read that result |
| Preprint "2605.30571" said at small batch, launch overhead is "the visible bottleneck" | The paper says memory-bound but not bandwidth-limited, and reports no per-kernel launch gap; it says the launch-bound observation is folk knowledge. It is one author's preprint |
| Licence "bans translation layers" | Item 8 bans reverse engineering generated output *for the purpose of translating it*; the phrase "translation layer" is the press's. Enforceability is unsettled and UNKNOWN to me |
| French probe: "one site reports it and nothing else does" | It is listed in Wikipedia's summary with a citation (a 2023 search of Nvidia's French offices, "graphics card sector"); I could not confirm it from the authority's site, and nothing ties it to CUDA. "Not confirmed" is right; "only one site" is not |
| "92% versus 30% compute use for prefill and decode" (a popular-article figure) | Primary preprint gives device-wide compute 92% in cold prefill and 7.9% in decode (arXiv 2609.12923, one H100, vLLM); keep the primary |
| Gartner 565 TWh, up 26% | I could not open Gartner; IEA and LBNL figures are in [power](research_02_power.md) |
| "Challenger chips mostly lose on software maturity", citing an eight-platform comparison (excerpts only) | I could not confirm this; the evidence I did read is AMD-specific and mixed (competitive at FP8 inference, behind at FP4 and in training) |

**Where Jarvis was right:** decode under-uses compute; the moat is the ecosystem more than the language; disaggregation is the incumbents' response; energy and grid limits are real.

## How far to trust this

- **Read verbatim, in part:** arXiv 2605.30571 (first third), 2609.12923 (first 42%), 2504.16112 (whole page), the 405B-parameter training report (through its reliability section), the CUDA EULA (about 44%), arXiv 2508.15734 (about 60%).
- **Search summaries only:** most prices, all India and regulator material, the IEA and LBNL numbers, all startup outcomes, the speculative-decoding numbers, the engine documentation.
- **Not reached:** Gartner, the IEA and LBNL pages themselves, regulators' sites, Reuters, the Tom's Hardware article body, any forum thread.
- **Not independently measured:** nothing here was tested by me. The numbers I added are arithmetic on cited figures, marked DERIVED.

## UNKNOWN, and who could answer

| question | who |
|---|---|
| Whether a production engine closes the 61% batch-1 gap | Engine maintainers; the founder's GPUs can test it |
| Fleet-level utilisation of inference | Hyperscalers, large neoclouds |
| Cost to migrate off CUDA | Teams that have ported |
| Whether the CUDA licence clause is enforceable against a runtime | Lawyers; courts |
| Any current regulator action on CUDA | The regulators' public registers |
| How small buyers decide | Direct interviews |
| Inference-fleet hardware failure rates | Cloud operators |

Related: [Research task 02](../vision_research_task_02.md), [Restart 2 study](../restart_2_weakness_study.md), [Research 01 summary](research_01_summary.md), [Vision review 01](vision_review_01.md), [Reviews index](README.md)
