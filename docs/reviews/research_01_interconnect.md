---
title: Research 01 - interconnect and scale-out (31 Oct 2026)
tags: [spark, review, research, interconnect, competitors]
---

# Research 01: interconnect and scale-out

Labels and read depth as in the [memory note](research_01_memory.md). Accessed 31 Oct 2026.

## What and why

| vendor | link | figures | label and source |
|---|---|---|---|
| Nvidia | NVLink 6 copper inside the rack | 3.6 TB/s per GPU; rack 216 or 260 TB/s (sources conflict) | VENDOR, [S] [Converge](https://convergedigest.com/nvlink-6-becomes-the-backbone-of-rubin-rack-scale-ai-architecture/), [S] [TweakTown](https://www.tweaktown.com/rss/click/news/114304/?c=news-mf) |
| Nvidia | Co-packaged optics in switches | 5x lower power, 4x fewer lasers | VENDOR, [S] [StorageReview](https://www.storagereview.com/news/nvidia-spectrum-x-ethernet-photonics-enters-full-production-with-4x-fewer-lasers-and-a-five-vendor-cpo-supply-chain) |
| general | energy per bit | co-packaged optics about 5 to 7 pJ/bit; active copper about 5 to 8 | THIRD-PARTY, [S] [Macroplane](https://macroplane.com/blog/co-packaged-optics). NVLink 6's own pJ/bit: UNKNOWN |
| Cerebras CS-4 | Ethernet fat tree between wafers | 3 microseconds (was 5), direct wafer link 2 microseconds; 2.4 Tb/s off-wafer | VENDOR via [P] [SemiAnalysis](https://newsletter.semianalysis.com/p/cerebrass-next-generation-cs-4-fast) |
| LP30 | Chip-to-chip links, 256 chips as one domain | NVLink support only from LP40 in 2028 | VENDOR, [P] [ServeTheHome](https://www.servethehome.com/decoding-the-future-of-inference-at-nvidia-groq-lpus-join-vera-rubin-platform-for-low-latency-inference/2/) |
| Google | Optically switched pods up to 9,216 chips | | VENDOR, [S] [summary](https://thenextweb.com/news/google-ironwood-tpu-inference-cloud-next) |

**Why it matters:** the Ma and Patterson paper argues that latency beats bandwidth for inference, since decode messages are frequent and small ([P] [paper, pages 5 to 6](https://arxiv.org/abs/2601.05047)). Reducing chip count by having more memory per chip also reduces hops. That conclusion favours dense memory, not more SRAM chips.

## What the buyer gets

InferenceX shows the rack-scale link paying off at low to medium per-user speed and losing its advantage at about 130 tokens/s per user on one test ([P] [InferenceX v2](https://newsletter.semianalysis.com/p/inferencex-v2-nvidia-blackwell-vs)). Note the same test: disaggregating prefill and decode beat aggregated serving at almost all interactivity levels, but on AMD FP4 it hurt at high interactivity for lack of tuned kernels. The network's value depends on software.

## Checks on this project's numbers

| project assumption | public comparison | reading |
|---|---|---|
| 0.5 microsecond per chip crossing | Cerebras reports 2 to 3 microseconds between wafers on shipping hardware | **The project is 4x to 6x lower than a shipping system.** A short board link may be faster, but a 630-chip system needs more than board links. Unverified; needs a design |
| 10 pJ/bit link energy | 5 to 8 pJ/bit | The project is conservative |
| 630 chips, about 11 per layer | LP30 uses 256 chips as one domain, for only 128 GB | Comparable class, at 2.5x the chips; no public example of a 630-chip scale-up domain by a startup was found |
| No GPU interconnect time in the model | V-02, V-14 | Still open in [Jarvis's response](jarvis_response_01.md) |

## Flaw, and what stops copying

- **Flaw:** every SRAM machine multiplies chips to gain capacity, and pays in hops and network cost. The Next Platform's author doubts that Cerebras supports over 2,048 nodes in one cluster (author's view, [P] [article](https://www.nextplatform.com/compute/2026/08/19/cerebras-overclocks-wse-3-waferscale-engine-to-boost-inference-oomph-in-nexus-cs-4/5289400)).
- **Cheapest fix for us:** do not build a network. Target models that fit on one card or one board, so no scale-out network exists at all. This reduces the addressable market, and nothing stops others copying it, but it removes a cost we could never fund.

## What they cannot do

Nvidia's scale-up domain ties buyers to its switches and rack power; a Rubin rack is reported at about 166 to 230 kW ([S] [sources conflict](https://www.spheron.network/blog/nvidia-vera-rubin-nvl72-guide/)). A buyer with an ordinary air-cooled room cannot host it. See [packaging](research_01_packaging.md).

Related: [Research summary](research_01_summary.md), [Packaging and cooling](research_01_packaging.md), [Reviews index](README.md)
