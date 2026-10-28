---
title: Concept study - how a GPU and its memory are built, and what we could change
tags: [spark, research, concept-study, accelerator, memory]
---

# Concept study: GPU and memory (28 Oct 2026)

Founder's request: study how a GPU is built and designed, and how its memory is created and designed, and whether changes would let us fit more memory into the chip, more efficiently. Method as in [the convolution card](concept_study_convolution.md): why it exists, how it is built, where it fails, then our own fix, tested before building. Labels: REASONING = general knowledge; REFERENCE = a number from a public source, not verified by us; ESTIMATED = our model. Papers and web pages are references only, never evidence of our results.

## 1. The GPU

**Why it exists (REASONING).** Graphics and later neural networks apply the same arithmetic to millions of independent items. A CPU spends most of its area on making one thread fast (caches, branch prediction, out-of-order logic); a GPU spends it on many simple lanes, and hides memory delay by switching between thousands of threads.

**How it is built (REFERENCE, H100 class).** The die is about 814 mm2 ([Wikipedia](https://www.Wikipedia.org/wiki/Nvidia_H100)) with 132 enabled streaming multiprocessors (SMs). Each SM has four tensor-core units, a 256 KB register file, and about 228 KB of combined L1 and shared memory; the chip has about 50 MB of L2 cache ([Chips and Cheese](https://chipsandcheese.com/p/nvidias-h100-funny-l2-and-tons-of-bandwidth), [BentoML](https://bentoml.com/llm/kernel-optimization/gpu-architecture-fundamentals)). Threads run in groups of 32 (warps) in lock step; the memory ladder is registers, shared memory, L2, then external HBM. I found no public per-block die-area breakdown.

**Where it is used.** Training and inference of large models, graphics, simulation.

**Its flaws and limits (REASONING, with our numbers).**

| flaw | evidence |
|---|---|
| The ladder exists because the big memory is far and costly to reach; most energy goes to moving data | tile model: compute is 1 to 12% of energy in memory-bound kernels ([tile study](L_numeric_tile_study.md), ESTIMATED) |
| Lock-step lanes waste work on zeros and on easy inputs | our sparse recognition skips 87% of inputs, 35.8x in the model (ESTIMATED) |
| Memory is copied up the ladder every time (HBM to L2 to shared to registers) | a design where the working set lives beside the compute avoids the copies |
| Only about 33 MB of its fastest storage (register files) and about 50 MB of L2; a 1 GB working set must stream from HBM | REFERENCE sizes above |

## 2. The memory

**SRAM (the on-chip memory).** Six transistors hold one bit; fast and compatible with logic, but big and leaky. The bitcell is 0.021 um2 at both N5 and N3E, so it has stopped shrinking ([Bits and Chips](https://bits-chips.com/article/going-from-n5-to-n3-sram-barely-scaled-at-tsmc/), [Tom's Hardware](https://tomshardware.com/news/no-sram-scaling-implies-on-more-expensive-cpus-and-gpus), REFERENCE). Flaw: area and leakage per bit.

**DRAM and HBM (the external memory).** One transistor plus a capacitor per bit, made on a separate memory process that is dense but slow and needs refresh. HBM stacks 4 to 16 DRAM dies over a base logic die joined by through-silicon vias, 1024 bits wide per stack, sitting beside the GPU on a silicon interposer ([Wikipedia](https://en.wikipedia.org/wiki/High_Bandwidth_Memory), [AnandTech](https://www.anandtech.com/show/18880)); a 24 GB 8-high stack is common. It is expensive because of the vias, the interposer, packaging and stack yield, and the interposer packaging capacity is a supply bottleneck (REFERENCE). Flaw: energy per bit and cost per bit rise as stacks go higher.

**Alternatives that put more bits in the same area (REFERENCE, from papers; none verified by us).**

| option | claim | catch |
|---|---|---|
| Gain cell (2T or 3T embedded DRAM) | about 1.5x (HyGain, after periphery) to 2x the density of 6T SRAM, and about half the dynamic energy ([HyGain](https://arxiv.org/pdf/2110.01208)) | refresh power; short retention |
| STT-MRAM | cell 2 to 3x smaller than high-density SRAM, non-volatile, low leakage | high write current |
| Stacking memory layers vertically (the idea behind 3D V-Cache) | density multiplies with layers; a proposal reports up to 22x ([DATE 2026](https://past.date-conference.com/proceedings-archive/2026/DATA/154.pdf), [monolithic gain-cell stack](https://arxiv.org/pdf/2503.06304)) | extra process steps, heat, cost per layer |

## 3. Can we fit more memory, more efficiently? (ESTIMATED, [memory_options_model.py](../hw/brain/experiments/month5/memory_options_model.py))

Base scenario of the [SRAM cost model](../hw/results/sram_area_cost_model.md); density multipliers taken from the table above, extra layer cost assumed at 0.6 of a die; refresh, write energy and speed not modelled. Silicon cost and footprint (including 150 mm2 logic):

| option | 1 GB footprint, cost | 4 GB cost | 44 GB cost |
|---|---|---|---|
| 6T SRAM | 491 mm2, $223 | $696 | $7,365 |
| gain cell 2x | 321 mm2, $124 | $352 | $3,663 |
| STT-MRAM 2.5x | 287 mm2, $107 | $276 | $2,869 |
| SRAM stacked 4 layers | 235 mm2, $235 | $624 | $5,089 |
| gain cell 2x stacked 4 layers | 193 mm2, $184 | $347 | $2,528 |

(The base-scenario table in the SRAM note shows 341 mm2 for SRAM alone; 491 mm2 here adds the 150 mm2 logic.)

Reading: these changes cut footprint and cost by 1.5 to 3x and reach about 1 GB in under 200 to 300 mm2. They do not close the 10-fold gap to HBM per byte, and they carry costs the model leaves out. So yes, more memory fits on chip with these changes, but the honest gain is about 2x, not an order of magnitude, until a stacked option is proved.

## 4. Our own directions (hypotheses, each to be tested before any build)

1. **Match the memory to the data, not one memory for all.** Our sparse tables are read-heavy and rarely written: a candidate for dense read-mostly cells (MRAM-like or gain cell) while the hot counters stay in SRAM. Test: split a workload's reads and writes in the tile model and price each part with its cell.
2. **Keep the working set in place.** The GPU copies data up a four-step ladder; the tile reads from banks beside the compute (already in the model). Test: add the interconnect cost of banks that are far from the compute, which the model omits.
3. **Skip, don't store, what is zero.** Store only active events (L's code is 13% active); the table is a sparse structure, so bytes per class shrink. Test: bytes per class of an event-indexed table against the dense one (MEASURABLE from the shipped code).
4. **Precision where it is needed:** mixed-precision storage (int8 bulk, rare high precision) shrinks the bytes that must fit. Already supported by the [primitive test](../hw/results/arithmetic_primitive_test.md).

## 5. Caveats and next test

No numbers here are measured. Density claims come from papers and press, extra costs are assumed, and speed and refresh are missing. Next test: direction 3 (bytes per class for an event-indexed table, a measurement on our own code), then direction 1 with a read/write split.

Related: [Numeric tile study](L_numeric_tile_study.md), [SRAM cost model](../hw/results/sram_area_cost_model.md), [Concept study: convolution](concept_study_convolution.md), [Docs index](INDEX.md)
