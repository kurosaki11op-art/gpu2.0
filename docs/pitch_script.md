# SPARK pitch: speaking script

Two versions: the **3-minute video script** (use this for the PYP video) and the **full slide notes** (for live presentations and Q&A, ~7.5 min).

## 3-minute video script (~420 words, 9 slides: cover, hook, twoplustwo, rootcause, evidence, solution, thinkless, proof, close)

**[cover]** We are [team name] from [college]. This is SPARK: a brain-inspired co-processor that makes AI do only the work a question needs.

**[hook]** Your brain runs on about 20 watts. One modern AI rack draws around 120 kilowatts. Data centres used 415 terawatt-hours in 2024, and that may double by 2030. Every joule becomes heat, and removing heat costs power and water. India's data centres could need 358 billion litres a year by 2030.

**[twoplustwo]** Much of that work is wasted. AI spends the same effort on "two plus two" as on a hard problem. Reasoning models write about fourteen times more tokens per answer, with up to fifty times more CO2. One study found only a quarter of questions even needed the big model.

**[rootcause]** The root cause is the chip. GPUs compute everything densely, and up to 84 percent of their energy can go on moving data, not computing. AI evolved to fit the GPU, not the brain.

**[evidence]** We hit this ourselves. We built L, a brain-like language model with spiking neurons and a memory that learns while it reads. It already beats a same-size transformer. But 95 percent of its neurons are silent, and the GPU still computes them all.

**[solution]** So we're building SPARK. It doesn't replace the GPU; it sits beside it, like Google's SparseCore beside the TPU. The GPU trains. SPARK runs brain-like AI with memory beside compute, 4-bit spikes, and on-chip learning and recall.

**[thinkless]** Its rule: think less, work less. Skip silent neurons. Skip neurons that didn't change. Recall instead of recomputing. Stop early when the answer is clear. Cap the energy per token.

**[proof]** Our prototype is one SPARK core on a 4,199-rupee FPGA. We'll prove identical output to the GPU, lower energy per token, and the saving from each switch, in watts and degrees.

**[close]** Less work means less power, less heat and less water. We don't claim to replace GPUs, and our prototype is small. But we can show AI that thinks only as hard as it needs to. Thank you.

---

## Full slide notes

## 1. cover  (~43 words)

Hello judges. We are [team name] from [college]. Our project is SPARK: a brain-inspired co-processor that works alongside GPUs and makes AI do only the work a question actually needs, so it uses less power, makes less heat and needs less cooling water.

## 2. hook  (~46 words)

Your brain runs on about twenty watts, the power of a dim light bulb. A single modern AI rack of 72 GPUs draws around 120 kilowatts. That's six thousand brains' worth of power for one rack. We asked: why is AI so far from the brain?

## 3. problem  (~77 words)

Data centres used 415 terawatt-hours in 2024. The IEA expects that to more than double by 2030. Every one of those joules becomes heat, and removing it costs more energy and water. India's data-centre water use may climb from about 150 to 358 billion litres a year by 2030, and Indian capacity is set to grow more than five times. Then the hardware becomes e-waste: generative AI alone could add 1.2 to 5 million tonnes by 2030.

## 4. twoplustwo  (~87 words)

Here's the waste we target. Today's AI spends the same effort on "two plus two" as on a hard problem. Reasoning models write about fourteen times more tokens per answer, with up to fifty times more CO2 per query. A paper literally titled "Do not think that much for 2 plus 3" shows models overthinking trivial questions. And one study found only 14 to 26 percent of questions needed the big model at all. Transformers run every layer for every token, and GPUs can't cheaply skip work.

## 5. rootcause  (~54 words)

The root cause is the hardware. GPUs were designed for graphics: dense, high-precision maths. One study found up to 84 percent of a GPU's dynamic energy goes on moving data around, not computing. Researchers call this the hardware lottery: AI ideas succeed when they fit the chip. Brain-like ideas didn't fit, so they lost.

## 6. principles  (~63 words)

We found six things the brain does that GPUs don't. The brain keeps memory beside compute; GPUs shuttle data off-chip. In the brain, silent neurons cost nothing; GPUs compute every neuron, even zeros. The brain uses low-precision signals and learns locally, while it reads. It recalls by association, and it has no central scheduler. Each of these becomes one block in our processor.

## 7. evidence  (~76 words)

We found this wall ourselves. We built L, a brain-like language model with no attention: spiking neurons, a memory that learns while it reads, and hippocampus-style recall. In early tests it beats a same-size transformer by about six percent and recalls text two thousand bytes back. Only 2 to 10 percent of its neurons fire, but the GPU computes all of them anyway, so our better model trains slower. The hardware is built for something else.

## 8. split  (~70 words)

We were careful here. Many GPU problems can be fixed in software: fused kernels, parallel scans, smaller number formats. We do those first, on the GPU. What's left can't be fixed in software: skipping silent neurons one token at a time, keeping memory beside compute, four-bit arithmetic, learning and recall on the chip, and scaling effort down for easy input. That remaining gap is our measured case for new hardware.

## 9. solution  (~71 words)

So we're not replacing the GPU. SPARK is a co-processor that sits beside it. The GPU keeps training and dense maths. SPARK runs brain-like models: an event-driven engine that computes only firing neurons, four-bit spikes, memory beside compute, a learning unit and a recall unit. There's precedent: Google added a small SparseCore to its TPU and got five to seven times faster sparse work for about five percent of the chip.

## 10. thinkless  (~83 words)

The heart of SPARK is one rule: think less, work less. Do nothing unless something changed, matters or is new. It skips silent neurons, neurons that barely changed, and idle neurons until they're needed. When the memory already knows the answer, it recalls instead of recomputing. When an early layer is confident, it stops. And a hard energy cap bounds the worst-case heat per token. Each of these is backed by published work, and each one we'll switch on and off to measure.

## 11. competition  (~108 words)

Others have built brain-inspired chips, and each leaves a gap. Intel's Loihi beats an H100 on energy for generation, but Intel's own survey says standard networks see little benefit, and access is research-only. IBM's NorthPole keeps memory beside compute, but the model must fit on the chip and it can't learn. Edge chips like Akida and Innatera only run small sensor models. Fast transformer chips need hundreds of chips or lock you into one architecture. SPARK is the first we know of to co-design a brain-like language model with its chip, including on-chip learning, recall and think-less skipping. Our gap: we still have to prove it at scale.

## 12. proof  (~64 words)

Our prototype is one SPARK core on a 4,199-rupee FPGA, running a small version of L byte by byte, with an ESP32 logging power and a sensor measuring heat. We'll prove three things: identical output to the GPU, lower energy per token, and the saving from each think-less switch, measured off versus on, on easy and hard text. Watts and degrees, not just claims.

## 13. viability  (~67 words)

The path is low-cost. Today, a six-thousand-rupee FPGA prototype with open measurements. Next, an edge module for always-on AI in machines and power grids, where every watt matters. Then, licensing the core as a co-processor tile, with tape-out supported by India's Design Linked Incentive scheme, which reimburses up to half of chip-design cost. Edge AI chips are forecast at roughly ten to twenty billion dollars by 2030.

## 14. impact  (~62 words)

The impact follows from physics. Less work means less power, and nearly every joule becomes heat, so less heat to remove and less cooling water. We'll measure power and heat directly on the prototype, and project water clearly labelled as an estimate. Better cooling and smarter scheduling remove heat more efficiently. SPARK removes it at the source, and the gains stack together.

## 15. close  (~77 words)

Our plan is sixteen weeks: software fixes and think-less modes first, then the core in Verilog, then the FPGA with real power and heat measurements. Our team covers AI, chip design, electrical power measurement, and mechanical heat and water modelling. And we're honest about limits: we don't replace GPUs, our prototype runs small models, and data-centre savings are projections until proven. Our goal is simple: AI that thinks only as hard as it needs to. Thank you.

---
Total ~1048 words (~7.5 min at 140 words/min).
