---
title: Tile mesh test - routers, a distributed matrix product and the traffic assumption
tags: [spark, result, simulated, rtl, l-forge, mesh]
---

# Tile mesh test (28 Oct 2026)

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

## Not covered

The all-to-all pattern of the FFT's transposes (needs a general router with arbitration and a measured contention cost), stencil halo exchange as its own test (it uses the same single-hop links, so the traversal result carries over, but contention and corner cases are untested), die-to-die links, the 2,048 to 43,000 tile scale, energy (only traversals are counted), and any clocking or physical effect.

Related: [Results index](INDEX.md), [Forge lane and traffic](forge_lane_and_traffic.md), [Virtual device tests](virtual_device_tests.md), [L Forge design](../../docs/L_forge_design.md), [Mesh RTL](../rtl/mesh/README.md)
