---
title: Paper notes index
tags: [l, research, papers]
---

# Paper notes index (full-text reading, 24 Oct 2026)

Read from the arXiv/OpenReview/NeurIPS PDF text with the network access opened on 24 Oct; numbers marked UNVERIFIED in each note could not be confirmed in the text. Paywalled IEEE/ACM and Nature papers were not reachable.

- [Tsetlin machine papers](tsetlin_papers.md): FPTM, CTM, Composites, Drop clause, CoTM; the exact FPTM input encoding (59,584 bits) and Fashion-MNIST rows.
- [Weightless network papers](weightless_papers.md): DWN, ULEEN, BTHOWeN; Fashion-MNIST 89.12% at 7.8 KiB, the training recipe and why free LUT tables are unstable.
- [Logic gate and LUT networks](logic_gate_lut_papers.md): difflogic, convolutional logic gate networks (CIFAR-10 86.29%), LogicNets, PolyLUT, NeuraLUT, TreeLUT, AdderNet; the residual-initialisation recipe.
- [Hebbian coding and label quality](hebbian_and_labels_papers.md): Fashion-MNIST dataset paper, label-error studies, BCPNN, SoftHebb; irreducible error is about 3 to 4%.
- [Continual learning and benchmarks](continual_and_benchmark_papers.md): Split MNIST / Split Fashion-MNIST baseline tables, MLPerf Tiny rules.
- [Adapting features without forgetting](forgetting_free_adaptation_papers.md): FlyModel, masks (SupSup, Piggyback, PackNet, HAT), recruitment (DEN), gradient projection (GPM, NSCL, OWM), FearNet, metaplasticity; ranking for a binary/integer chip.
- [Synthesis: what the papers mean for L](../papers_synthesis.md)
- [Exemplar-free class-incremental A](exemplar_free_papers_a.md): FeTrIL (feature translation), SDC (drift compensation)
- [Exemplar-free class-incremental B](exemplar_free_papers_b.md): SSRE, EFC (cold start)
- [Exemplar-free class-incremental C](exemplar_free_papers_c.md): FeCAM, ADC
- [Exemplar-free class-incremental D](exemplar_free_papers_d.md): C-FSCIL (hyperdimensional prototypes), AdaGauss (why exemplar-free fails), exemplar-free survey
- [Exemplar-free class-incremental E](exemplar_free_papers_e.md): generative and feature replay
- [Exemplar-free class-incremental G](exemplar_free_papers_g.md): few-shot class-incremental and growing prototypes
- [Exemplar-free class-incremental H](exemplar_free_papers_h.md): neurogenesis, expert gates and expandable representations
- [Exemplar-free class-incremental L](exemplar_free_papers_l.md): novelty and out-of-distribution detection for old-versus-new decisions
- [Exemplar-free class-incremental F](exemplar_free_papers_f.md): frozen features with prototypes and random projections
- [Exemplar-free class-incremental I](exemplar_free_papers_i.md): local learning rules and forgetting
- [Exemplar-free class-incremental K](exemplar_free_papers_k.md): sparse associative memories and weightless incremental learning
- [Exemplar-free class-incremental J](exemplar_free_papers_j.md): minimal memory baselines and the theory of forgetting
- [Synthesis: exemplar-free class-incremental learning](../exemplar_free_synthesis.md): what 25 papers say and the tests they suggest
- [Stanford memory A](stanford_memory_a.md): compressed and sparse inference hardware (EIE, Deep Compression, pruning, survey)
- [Stanford memory b](stanford_memory_b.md): IO-aware algorithms and memory hierarchy at scale (FlashAttention, Monarch, SN40L)
- [Stanford memory d](stanford_memory_d.md): memory-centric and in-memory accelerators (Stanford hardware groups)
- [Stanford memory c](stanford_memory_c.md): state size, recall and throughput in efficient sequence models (H3, Zoology, Based, Mamba)
- [Onchip memory chips a](onchip_memory_chips_a.md): on-chip memory designs of Cerebras, Groq and Graphcore (some sources blocked)
- [On-chip and in-memory compute designs (Dojo, Tenstorrent, d-Matrix, macros, xAI check)](onchip_memory_chips_b.md): sources partly blocked; Tenstorrent atomic counters, in-memory macros, xAI finding
- [Study: memory technology study](memory_technology_study.md): memory technologies, scaling limits and energy per bit (14 arXiv papers)
- [Study: nvidia blackwell study](nvidia_blackwell_study.md): NVIDIA data-centre GPU architecture up to Blackwell (vendor pages blocked; specs second-hand)
- [Study: Cerebras wafer-scale engine in depth](cerebras_study.md): about 22 arXiv papers read; vendor whitepapers blocked
- [Thinking research 2: working memory and steps over time](thinking_research_2_working_memory.md): matrix-free state carried between steps (in progress, full reads being completed)
- [Thinking research 1: imagination without backprop](thinking_research_1_imagination.md): generators that keep how features combine (in progress, full reads being completed)
- [Thinking research 3: hypothesis, test and keep](thinking_research_3_hypothesis_loop.md): propose-test-keep loop on counted contrasts (in progress, full reads being completed)
- [Thinking research 4: goals and intrinsic motivation](thinking_research_4_goals.md): bounded drives for the controller (in progress)
- [Thinking research 5: symbols and composition](thinking_research_5_composition.md): binding and composition with matrix-free operations (in progress, full reads being completed)

Related: [Research notes](../notes/INDEX.md), [Research report](../matrix_free_vs_cnn_report.md), [Docs index](../../INDEX.md)
