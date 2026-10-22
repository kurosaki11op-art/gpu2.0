# Brain as a chip: what is known, what is not, and what L can take from it

Method: web search on 2026-10-11. Figures come from the cited pages' search excerpts, not full-paper reads, and the
vendor figures are vendor claims. Treat everything here as RESEARCH CONTEXT, not an L result.

## 1. What we know about the brain (and what limits copying it)

| Fact | Source / status |
|---|---|
| ~86 billion neurons in a human brain (not 100 billion) | [Herculano-Houzel's cell counting, summarised at BrainFacts](https://www.brainfacts.org/in-the-lab/meet-the-researcher/2018/how-many-neurons-are-in-the-brain-120418) |
| Brain uses ~25% of the body's energy, about 500 kcal/day; that is roughly 20–25 W (my arithmetic) | [NYRB piece on the 86-billion count](https://www.nybooks.com/articles/2016/11/24/86-billion-neurons-herculano-houzel/) |
| Synapse count (~10^14 or more) was NOT confirmed by this search; treat as an unverified estimate | not sourced here |
| One cubic millimetre of mouse visual cortex mapped: ~84,000 neurons, ~0.5 billion synapses, ~5.4 km of wiring, paired with activity recordings | [Scientific American on the 2025 MICrONS papers](https://www.scientificamerican.com/article/biggest-brain-map-ever-shows-mouse-neurons-in-stunning-detail/), [NIH release](https://www.nih.gov/news-events/news-releases/scientists-map-unprecedented-detail-connections-visual-perception-mouse-brain) |
| That map reportedly took ~US$100 million and 100+ scientists; the human mm³ comparison had ~16,000 neurons | same sources |

Reading: we have the first wiring-plus-activity map of one cubic millimetre of a mouse, so a whole human brain's wiring is far away.

## 2. We do not know the brain's learning algorithm

- A [2024 review of neuroscience-inspired ML](https://arxiv.org/html/2403.18929v1) lists the candidates: predictive coding, contrastive Hebbian learning, forward-only learning, equilibrium propagation.
- [A 2026 review](https://arxiv.org/pdf/2608.19995) argues that none yet matches backpropagation's combined scalability, generality and hardware fit. I did not open the full text.
- Backpropagation's problems for biology: error signals are not local to a synapse, it needs symmetric forward and backward weights, and it does not fit spiking neurons.

Consequence: copying the brain's hardware without its algorithm gives something that cannot be trained to do what an LLM does.

## 3. What exists in silicon

| System | Reported scale | Caveat |
|---|---|---|
| [Intel Hala Point (Loihi 2)](https://newsroom.intel.com/artificial-intelligence/intel-builds-worlds-largest-neuromorphic-system) | 1.15 billion neurons, 128 billion synapses, 1,152 chips, max 2,600 W; 15 TOPS/W "early results" on deep networks | Vendor claims; Intel says its neuron count is about an owl brain or a capuchin monkey cortex, and it is not meant for neuroscience modelling |
| [SpikeLLM, ICLR 2025](https://arxiv.org/abs/2407.04752v3) | Spiking encoding of a 7B LLM, W4A4: 11% lower WikiText2 perplexity than the OmniQuant baseline, +2.6% reasoning accuracy | Accuracy results, not measured joules per token |
| [SpikingBrain](https://arxiv.org/html/2509.05276v3) | Spiking, hybrid-attention large models with INT8 weights and KV cache; a third-party summary reports >100× speed-up at 4M-token contexts | The 100× figure is second-hand; check the paper before quoting |
| [Charge-based analog/digital attention chip, 65 nm](https://arxiv.org/pdf/2409.04940) | Fabricated; 14.8 / 1.65 TOPS/W (analog core / SoC); prunes ~3/4 of tokens with <0.38% accuracy loss | Small model class; different workload than an LLM |
| [Gain-cell in-memory attention](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12457188/) | Simulated: up to 100× lower attention latency and 10,000× lower energy than GPUs | Simulation only; needs special initialisation because analog circuits are non-ideal |

Reading: brain-like hardware is real and improving, but best systems are about 1% of a human brain's neurons, and LLM-class results on it are early.

## 4. What transfers to L and to helping GPUs now

1. **Event-driven work** (do nothing when nothing changes): L already does this.
2. **Compute next to memory**: the GPU's wall is memory bandwidth (H020). Analog and in-memory attention is the research route; the token-pruning chip above shows a digital version is buildable today.
3. **Pruning before heavy compute**: the analog chip cuts ~75% of tokens before the digital part. L's analogue is cutting what the GPU must verify via drafts and confidence.
4. **Spiking LLM encodings** (SpikeLLM, SpikingBrain) are a way to put real LLM layers on event-driven hardware, but results so far are about accuracy and speed, not measured energy.

## 5. Roadmap that stays honest

| Stage | What | Evidence needed |
|---|---|---|
| Now | L as a decode co-processor beside the GPU (copy engine + tree drafts + calibrated draft length) | Real-model acceptance (done, 2.2–2.3 tokens/pass), then timed end-to-end speed and wall-plug joules |
| Next | Multi-stream, multi-chip L on FPGA, then larger simulation | Measured throughput per stream and per watt |
| Research | Event-driven, compute-near-memory tiles for pruning and attention | Compare to the fabricated analog/digital attention chip above on the same tasks |
| Vision | Brain-scale event-driven hardware | Not claimed. Needs a known learning algorithm and a model class that trains on it |
