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

## Papers, community and repository leads on GPU problems (1 Nov 2026; web-search summaries, unverified until the sources are read)

- **Hardware limits papers:** Ma and Patterson, [arXiv 2601.05047](https://arxiv.org/pdf/2601.05047) (compute up 80x in a decade against memory bandwidth up 17x; $/GB and $/GBps of HBM rising; proposes high-bandwidth flash; multi-chip sharding means frequent small messages); an NVIDIA research limit study, [arXiv 2507.14397](https://arxiv.org/html/2507.14397v2) (bandwidth, compute, synchronisation and capacity as the barriers; one decoded token can need the capacity and bandwidth of many chips); a roofline survey, [arXiv 2402.16363](https://arxiv.org/pdf/2402.16363) (processing-in-DRAM suits small batches only; limited capacity).
- **Expert routing (relevant to step 22):** [ExpertFlow](https://arxiv.org/html/2410.17954) reports 91.96% cache hit rate from predicting routing; [MoE-Beyond](https://arxiv.org/html/2508.17137v1) lifts hit rate from 17% to 72% with 10% of experts cached but shows near-uniform aggregate popularity; an ICLR 2026 paper on [local routing consistency](https://iclr.cc/virtual/2026/poster/10011732) (20 models; most balance cache effectiveness and efficiency with a cache about twice the active experts); a single-author [blog measurement](https://insiderllm.com/guides/qwen-3-6-moe-expert-routing-measured/) of 87.6% to 93.0% hit rates on one model. The sources disagree on skew; hit rates depend on prediction and on time locality.
- **Community (secondhand, mostly blogs and mirrors):** VRAM capacity and memory bandwidth are the main complaints on r/LocalLLaMA (for example the gap between 16 GB cards and 27B-class dense models; "tokens per second is about bandwidth over model size" as the rule of thumb) ([summary](https://verum-research.pages.dev/localllama-research/), [guide](https://devbytes.co.in/news/understanding-gpu-memory-bottlenecks-for-local-llm-inference)). Memory supply: DRAM price up about 90% in Q1 2026 and HBM at 50% to 60% of GPU manufacturing cost per vendor and secondary sources ([Weka](https://www.weka.io/learn/ai-ml/ai-memory-wall/), [SoftwareSeni](https://www.softwareseni.com/hbm-the-chip-nobody-planned-for)): vendor claims.
- **Repository and forum issues:** vLLM issue [38887](https://github.com/vllm-project/vllm/issues/38887) (one request at 9.2 tokens/s with 1.9% cache use), a forum thread on [low GPU utilisation when processing whole batches](https://discuss.vllm.ai/t/why-vllm-cannot-fully-use-gpu-in-batch-processing/305) (cure: continuous batching), and a note that speculative-decoding gains fall as batch size grows ([PR 2607](https://github.com/vllm-project/vllm/pull/2607)).
- **Not found:** an actual Hacker News thread on these topics.

## Routine

Re-check monthly: Cerebras, Nvidia, AMD, Google, OpenAI hardware, Groq, Fractile, SRAM and wafer-scale papers (Hot Chips, ISSCC), and Rust in AI tooling. Offer: a scheduled monthly check can be created if the founder wants it.

Related: [Deep study plan](gpu_deep_study_plan.md), [Wafer price research prompt](wafer_price_research_prompt.md), [Vision review 01](reviews/vision_review_01.md), [Docs index](INDEX.md)
