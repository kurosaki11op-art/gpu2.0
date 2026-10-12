# Parallel "thought branches" in SPARK: what we can build and prove, and what we cannot

Responds to the "System 2 / AGI substrate" brief. Labels: MEASURED / SIMULATED / ESTIMATED (arithmetic on stated assumptions) / PROJECTED.

## 1. Reality check on the brief

| Claim in the brief | Check | Verdict |
|---|---|---|
| A GPU "grinds to a halt" on 10,000 parallel branches because every token re-fetches the weights | Weight reads are per decode *step*, not per branch. All branches in a batch share one read. 9B fp16 weights = 18 GB = about 22 ms per step on a 4090, whatever the branch count (ESTIMATED roofline, our own `draft_v4.py` assumptions). | Wrong as stated |
| The real GPU limit for wide search | The KV cache. 0.30 GB per 2,048-token branch for a 9B-class model (ESTIMATED). 64 branches = 19 GB, 256 = 77 GB, 1,024 = 309 GB; only about 20 fit on a 24 GB card after the weights. Reading the KV also costs about 96 ms/step at 256 branches, 4x the weight read. | The true bottleneck |
| The software fix already exists | Branches of one search tree share their prompt; storing only each branch's private suffix (64 tokens = 9 MB, ESTIMATED) lets about 600 branches fit in 6 GB. This is prefix sharing and tree attention in current serving stacks. | Software is ahead of us here |
| A neuromorphic chip generates tokens "orders of magnitude" faster | No neuromorphic chip has run a transformer LLM at GPU quality. Second-hand reviews report a MatMul-free LM on Loihi 2 at 41.5 tokens/s, and IBM's digital NorthPole at 28,356 tokens/s for a 3B model on 16 cards (vendor-reported). Putting weights "inside the neurons" needs the whole model on-chip: 3B at 8-bit = 3 GB; NorthPole holds 224 MB per chip. | Unsupported |
| "The hardware substrate required for AGI" | Nothing we or the reviews have shows AGI is limited by this. | Do not claim |
| FPGA prototype proves System 2 reasoning | Reasoning needs a trained model and a verifier. LIF cores without one reason about nothing. | Cannot be shown by this prototype |

What survives: search-heavy inference (best-of-N, tree search, speculative trees) is a real and growing workload. Its costs are KV memory and repeated prefix compute. A co-processor can help with branch management and drafting. It cannot replace the GPU's verification.

## 2. What we can honestly build: a branch-parallel draft engine

Prototype target: a small FPGA, drafting a tree of candidate continuations for a GPU to verify losslessly. Sizes are ESTIMATES for a 64-branch build.

| Block | Role | Size / note |
|---|---|---|
| Host interface | Commands ROOT(context), STEP, FORK(parent,k), PRUNE(id), READ_TOP(k); returns a draft tree {node, parent, token, score} | UART first, PCIe later |
| Branch table | Per branch: parent id, depth, cumulative confidence, state slot, history pointer, alive bit | 64 entries x ~16 B |
| State banks | Membrane state per branch: 2 layers x 128 neurons x 16 bit = 4 KB | 64 branches = 256 KB, fits FPGA block RAM |
| Weight store | Shared by all branches, stationary next to the lanes | about 50 KB at 4-bit for our v0 model |
| LIF lanes (tiles) | Take (branch id, token), read that branch's state, update, output top-k with calibrated confidence | replicate tiles to scale |
| Recall unit | Shared fast hash tables (existing) plus a per-branch history ring; branch history = parent's history + private suffix | prefix sharing in hardware |
| Tree manager | Score, keep top-W per depth, prune, free slots; on GPU feedback keep the accepted path and drop the rest | W = beam width |

**Fork** copies a 4 KB state: about 256 cycles with a 128-bit port, against roughly 2,000 cycles for a network step, so about 10% overhead (ESTIMATED).

**Data flow, one round:** host sends the context; the root branch steps; the tree manager forks the top-W candidate tokens; tiles step all live branches interleaved with branch-id tags; the manager prunes by cumulative confidence; the draft tree goes to the GPU; the GPU returns the accepted path; the manager promotes it and prunes the rest; repeat.

**Memory map (prototype):**

| Region | Contents |
|---|---|
| 0x0000 | control and status registers |
| 0x1000 | weight store (read-only after load) |
| 0x2000 | recall tables (shared) |
| 0x3000 | branch table |
| 0x4000 | history ring |
| 0x8000 | state banks, 4 KB per branch |

**NoC:** at this size we do not need one. Dense 128x128 layers fit one tile, so a shared bus or small crossbar carrying address-event packets {branch id 8 b, neuron id 7 b, value 3 b} is enough. A 2D mesh with XY routing becomes a real design item only if a layer is split across many tiles (roughly beyond 64 tiles). Building it now would be effort with no result to show.

## 3. What this can prove, and what it cannot

Can prove (each a measurable number):
1. **Branch scaling:** branch-steps per second against number of tiles (1, 2, 4, 8). Cycles per branch-step as branches grow.
2. **Branch management cost:** fork and prune cycles, state bytes per branch, maximum branches per FPGA (area).
3. **Tree value:** accepted tokens per GPU pass against tree width W (1, 2, 4, 8). The software harness already gives single draft 1.70 and multi-draft 2.28 on the real 3B model (MEASURED, acceptance only).
4. **End to end:** wall-clock tokens/s and energy against the best software drafter. Still needed and unmeasured.

Cannot prove: reasoning ability, AGI relevance, "orders of magnitude" token speed, replacing GPUs.

Investor-safe sentence: "A branch-parallel drafting engine that manages many speculative continuations in hardware, with measured acceptance on real models and a measured cost per branch."

## 4. Order of work

1. Tree-width sweep in software on the real 3B model (cheap, uses the existing harness).
2. The two missing real-model numbers: wall-clock timing and an end-to-end oracle test.
3. RTL for the branch table, state banks and tree manager, simulated against the golden model, then FPGA.
