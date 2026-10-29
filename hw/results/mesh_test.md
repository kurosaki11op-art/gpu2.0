---
title: Tile mesh test - routers, a distributed matrix product and the traffic assumption
tags: [spark, result, simulated, rtl, l-forge, mesh]
---

# Tile mesh test (28 Oct 2026)

(Two tests: the distributed matrix product with deliver-and-forward routers, and the FFT all-to-all transpose with general routers, further down.)

First check of the tile-to-tile assumptions behind the 2 GB design, in RTL: a P x P mesh of L Forge tiles with routers ([hw/rtl/mesh](../rtl/mesh/README.md)) runs a distributed matrix product; every output is compared with the lane golden model. **SIMULATED (iverilog); a small mesh (4 to 64 tiles), one pattern (row and column broadcasts); not the 2 GB array.**

## Results

| mesh | C and K | outputs differing from the golden model | communication + compute cycles | speedup over one tile (ideal) | lane busy over the run | link traversals per delivered word |
|---|---|---|---|---|---|---|
| 2 x 2 (4 tiles) | 8 x 8, K 64 | 0 of 64 | 12 + 69 = 81 | 3.2x (4x) | 79% | 1.00 |
| 4 x 4 (16 tiles) | 16 x 16, K 128 | 0 of 256 | 28 + 133 = 161 | 12.7x (16x) | 80% | 1.00 |
| 4 x 4, bigger tiles | 32 x 32, K 128 | 0 of 1,024 | 52 + 517 = 569 | 14.4x (16x) | 90% | 1.00 |
| 8 x 8 (64 tiles) | 32 x 32, K 256 | 0 of 1,024 | 60 + 261 = 321 | 51.0x (64x) | 80% | 1.00 |
| 8 x 8, small tiles | 16 x 16, K 128 | 0 of 256 | 18 + 37 = 55 | 37.3x (64x) | 58% | 1.00 |

Error against fp64 is 1.0e-2 to 1.2e-2 in every case, as for a single tile.

## What it shows (SIMULATED)

1. **The mesh computes the right answer bit for bit**, including the routers' deliver-and-forward behaviour, the priority of forwarding over injection and the global barrier; no flit was lost and no tile deadlocked at 4, 16 and 64 tiles.
2. **The traffic assumption holds for this pattern:** with deliver-and-forward routers each word crosses exactly one link per delivered copy (1.00 traversals per delivered word), which is what the fabric traffic model assumed for pipelined broadcasts (matrix multiply, and by the same argument the neighbour exchanges of stencils). Plain unicast copies would cost about (p + 1) / 3 times more hops (1.7 times at p = 4, 11 times at p = 32), so **the routers must support forward-while-delivering**; a router without it breaks the model's 3.9x matrix-multiply figure.
3. **The model left out a time cost:** communication is not overlapped with compute here, and takes 17 to 19% of the cycles at these tile sizes (communication cycles grow with the mesh dimension, 28 at p = 4 and 60 at p = 8, compute with the work per tile), so the mesh reaches about 80% of the ideal speedup, 90% with bigger tiles per mesh node and only 58% with very small ones. Overlapping the phases (not built) would recover most of it. The links are assumed one block word (136 bits) wide per cycle; with 32-bit links the communication cycles would be about 4 times longer.

## FFT all-to-all through general routers (SIMULATED RTL for the network, bit-exact lane model for the arithmetic)

[fft_alltoall.py](../rtl/mesh/fft_alltoall.py) with [gr_tile.v](../rtl/mesh/gr_tile.v): a distributed 2D DFT of N x N complex data (4 rows per tile) on a P x P mesh. Row DFTs per tile, block floating-point packing of the 4 x 4 complex sub-blocks, then the **all-to-all transpose in RTL** (every tile sends one block, two 136-bit flits, to every other tile; general routers: dimension-order routing, 4-flit input buffers, round-robin arbitration, back-pressure), then column DFTs. Checked: every delivered word, the final result against the same pipeline computed without the mesh, and the error against numpy's fft2.

| mesh | transform | flits | words differing from the intended words | final result identical to the no-mesh pipeline | error vs fft2 | cycles for the transpose (lower bound) | link traversals per flit (mean distance) | mean latency | blocked flit-cycles per flit |
|---|---|---|---|---|---|---|---|---|---|
| 2 x 2 | 16 x 16 | 24 | 0 | yes | 1.4e-2 | 15 (6) | 1.33 (1.33) | 5.5 | 0.4 |
| 4 x 4 | 64 x 64 | 480 | 0 | yes | 1.5e-2 | 98 (32) | 2.67 (2.67) | 20.5 | 3.5 |
| 8 x 8 | 256 x 256 | 8,064 | 0 | yes | 1.3e-2 | 632 (256) | 5.33 (5.33) | 40.1 | 6.8 |

What it shows (SIMULATED):
1. **The general routers deliver an all-to-all pattern correctly**: all 8,064 words at 64 tiles arrived intact at the right slot, with no loss or deadlock, and the transform equals the one computed without the mesh.
2. **The hop assumption of the traffic model holds:** link traversals per flit equal the mean Manhattan distance between distinct tiles (2.67 at 4 x 4, 5.33 at 8 x 8, which is 2p/3), the figure used for the FFT's fabric energy. Buffer and arbitration energy are not counted.
3. **Contention is real but moderate:** the transpose takes about 2.4 to 3 times the bisection-bandwidth bound (33% to 41% of the best possible); each flit waits 3.5 to 6.8 cycles in buffers on average; latency grows with the mesh (20 and 40 cycles).
4. **Whether the transpose matters depends on the FFT mapping.** With the matrix-product DFT used so far (about 8 to 21 times more lane operations than an ideal FFT) the transpose is 1 to 2% of the compute time (98 cycles against about 4,100 per DFT phase at 64 x 64; 632 against about 65,000 at 256 x 256). With a dedicated butterfly path that removes that overhead, compute shrinks 8 to 21 times and the transpose becomes roughly 10 to 25% of the time, unless it is overlapped.

## Not covered

Stencil halo exchange as its own test (it uses the same single-hop links, so the traversal result carries over, but contention and corner cases are untested), die-to-die links, the 2,048 to 43,000 tile scale, energy (only traversals are counted), and any clocking or physical effect.

## Communication overlapped with compute (29 Oct 2026, SIMULATED RTL)

[mesh_tile_pipe.v](../rtl/mesh/mesh_tile_pipe.v) and [gen_and_check_pipe.py](../rtl/mesh/gen_and_check_pipe.py) (log [mesh_pipe_results.log](../rtl/mesh/mesh_pipe_results.log)): the tile has two operand banks; in a stream of independent matrix products, while the lane computes product t from one bank the routers deliver the operands of product t+1 into the other. The accumulation order inside a product is unchanged, so the answers stay bit-exact with the lane golden model (reordering the K sum inside one product would change the numerics and was deliberately not done). The same hardware and data run twice, sequential (communicate, compute, next) and overlapped, and every output of every product is checked:

| mesh | products | outputs mismatching (both runs) | cycles sequential -> overlapped | saved | link traversals |
|---|---|---|---|---|---|
| 2x2 | 3 | 0 of 192 | 249 -> 223 | 26 (10.4%) | identical (192) |
| 4x4 | 6 | 0 of 1,536 | 978 -> 833 | 145 (14.8%) | identical (4,608) |
| 8x8 | 3 | 0 of 3,072 | 969 -> 847 | 122 (12.6%) | identical (21,504) |

The saving equals (products - 1) times the communication time of one product (13, 28 and 60 cycles at the three sizes), as expected: only the first product's communication cannot be hidden. For long streams the saving approaches the communication share of 17 to 19% found above, so the cost of communication is recovered almost completely when the work is a stream of products (layers, iterations). It does not help a single isolated product; overlapping inside one product would need the lane to load a partial accumulator (K-slice order), which is not built. Limits: only matrix products are tested; the stream uses independent operands per product; compute must be at least as long as communication, which holds at these tile sizes.

Related: [Results index](INDEX.md), [Forge lane and traffic](forge_lane_and_traffic.md), [Virtual device tests](virtual_device_tests.md), [L Forge design](../../docs/L_forge_design.md), [Mesh RTL](../rtl/mesh/README.md)
