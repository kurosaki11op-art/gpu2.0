---
title: Research task 04 for Vision - what GPU buyers actually pay for, and what Jevons paradox implies (1 Nov 2026)
tags: [spark, review, research, prompt, demand, paid-categories, jevons, vision]
---

# Research task 04 for Vision (1 Nov 2026)

Founder's change of focus (1 Nov 2026): efficiency alone is not what companies pay for (Jevons paradox: cheaper compute raises total use; the market rewards access to powerful GPUs and infrastructure). **Find the real GPU problems that companies pay for.** Vision's role is evidence and attack, not idea generation: do not propose products; report what is paid for, by whom, how much, and what the evidence is. Jarvis's candidate list will be attacked afterwards.

Repository: <https://github.com/kurosaki11op-art/gpu2.0>. Read branch `claude/sharp-davinci-wrwazg`; work on a new branch `vision/research-4`; write only in `docs/reviews/` (`research_04_<topic>.md`, `research_04_summary.md`). Standing rules: label every number (MEASURED / SIMULATED / MODELLED / ESTIMATED / PROJECTED; quoted figures PUBLISHED / VENDOR CLAIM / THIRD-PARTY ESTIMATE / UNKNOWN), source link and date for each, UNKNOWN instead of guessing, primary pages first, no AI model identifiers in repository content (describe models by size and type).

## Questions

1. **Jevons paradox in AI inference:** primary evidence that falling cost per token raised total use (token volumes, price history, provider statements, filings); counter-evidence; what it implies for a seller of efficiency (does efficiency sell more, or only enable more use by someone else?). Say how strong the evidence is.
2. **Categories of GPU-related software and services that companies pay for,** with evidence of payment: price lists, funded rounds, acquisitions and their reported sizes, public customer counts, revenue where disclosed. Include at least: GPU orchestration and scheduling, GPU sharing and multi-tenancy, utilisation and cost visibility, serving and inference platforms, reliability and failure recovery, GPU brokerage and marketplaces, on-premises deployment and support, data-centre power and cooling software. For each: typical customer, price or pricing model, free alternatives and how far they go, switching cost, who dominates, and the evidence label.
3. **What is accessible to a small team with no capital:** for each category, what a two-person team could build and test in weeks with a laptop GPU and free cloud GPUs, and what it could not.
4. **India:** the government-backed GPU compute programmes (what exists, how many GPUs, who can use them, how providers are chosen), Indian GPU clouds and what they say they lack, and Indian startups in these categories with funding evidence. Primary pages only; mark everything else a lead.
5. **Who pays and who decides:** buyers in each category and how they buy (self-serve credit card, enterprise sales, tender), with evidence.
6. **Verdict table:** category by evidence of payment (strong / weak / none), accessibility for a small team, competition, and the cheapest experiment that could kill it.

## Deliverables

One note per topic, a summary with the verdict table, a list of corrections to Jarvis's first sketch ([restart note](restart_2_weakness_study.md) and the founder's conversation categories: GPU scheduling and sharing, utilisation and cost visibility, failure recovery, serving setup for small clouds), and a list of UNKNOWNs with who could answer.

## Limits

Public sources only; do not contact companies; do not treat Jarvis's numbers or recollections (for example the size of one acquisition and the scale of an Indian programme) as true: they are unverified.

Related: [Research task 03](vision_research_task_03.md), [Research 03 summary](reviews/research_03_summary.md), [Restart 2 study](restart_2_weakness_study.md), [Docs index](INDEX.md)
