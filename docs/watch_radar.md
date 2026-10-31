---
title: Watch list - Rust in AI and new GPU / accelerator news (started 31 Oct 2026)
tags: [spark, gpu, radar, rust, competitors]
---

# Watch list (31 Oct 2026)

Founder asked to take Rust's rise in AI into account and to keep watching GPU news and research. Entries are from web searches, mostly blogs and aggregators: treat every item as **UNVERIFIED** until a primary source (company release, filing, paper) is checked. Add a dated line per check.

## Rust in AI

- Search found a Rust trend in AI agent runtimes and developer tools (OSSInsight analysis, Q1 2026; Hugging Face Candle as a Rust ML framework; general Rust adoption surveys). **I found nothing confirming that OpenAI itself is moving to Rust**; to check: OpenAI engineering posts, job postings, public repositories.
- Consequence for us: the simulator, the cost model and the tile checks are already Rust (standard library only), so the toolchain direction matches. Python stays for exporting and training models. A compiler front end in Rust is a candidate for M4.

## Competitor and hardware news (to check against primary sources)

- Cerebras: CS-4 (three wafer-scale processors, N5, claimed up to 30x faster inference than GPU systems; availability Q3 2026 per Reuters via a summary), a roadmap whose CS-6 reportedly adds **stacked DRAM** (relevant: our design is SRAM-only), an IPO filing, a reported AWS deal. Check the claims against Cerebras's own materials.
- Nvidia Vera Rubin (reported in full production) and Rubin CPX for large-context inference; AMD reported to pair a future GPU with Cerebras's engine; Qualcomm AI200 and AI250 (announced October 2025); Google new inference chips (undated, no detail); OpenAI custom accelerator with Broadcom; other autumn 2026 inference chips (Intel, Fractile).
- Consequence for us: the current-generation GPU column that Vision asked for (V-17) should use Rubin-class figures from primary sources, and our speed claims face wafer-scale rivals that already ship, not only GPUs.

## Routine

Re-check monthly: Cerebras, Nvidia, AMD, Google, OpenAI hardware, Groq, Fractile, SRAM and wafer-scale papers (Hot Chips, ISSCC), and Rust in AI tooling. Offer: a scheduled monthly check can be created if the founder wants it.

Related: [Deep study plan](gpu_deep_study_plan.md), [Wafer price research prompt](wafer_price_research_prompt.md), [Vision review 01](reviews/vision_review_01.md), [Docs index](INDEX.md)
