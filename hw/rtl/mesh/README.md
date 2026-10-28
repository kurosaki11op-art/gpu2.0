---
title: L Forge tile mesh (routers and a distributed matrix product), RTL check
tags: [spark, rtl, l-forge, mesh, hardware]
---

# L Forge tile mesh (hw/rtl/mesh)

`mesh_tile.v`: a tile with local memory, one `forge_lane` and a small router, for a P x P mesh. A matrix product C = A B is distributed SUMMA-style: tile (I,J) holds A(I,J) and B(I,J); in a communication phase every tile sends its A words east and west and its B words south and north, and the routers **deliver each arriving flit to the local memory and forward it onward** (forwarding has priority over injection); one flit (a 136-bit block word plus a header) per link per cycle. A global barrier then starts the compute phase, in which each tile multiplies its assembled A row and B column with the lane. The router serves these row and column broadcasts only: it has no general addressing and no arbitration between independent flows.

`gen_and_check.py [P] [MT] [NT] [NBT]` generates the mesh for the given size, runs it in iverilog and compares every output (mantissa and exponent) with the lane golden model. Results: [Mesh test](../../results/mesh_test.md).

`gr_tile.v` is the **general** version: a 5-port router with dimension-order (X then Y) routing, 4-flit input buffers, round-robin arbitration and ready-based back-pressure, plus an endpoint that injects flits from a list and stores arrivals by slot. `fft_alltoall.py [P]` runs a distributed 2D DFT whose all-to-all transpose goes through these routers in RTL (the DFT arithmetic uses the bit-exact lane model) and checks every delivered word, the final result and the network cost.

Related: [Hardware index](../../HARDWARE_INDEX.md), [Forge RTL](../forge/README.md), [Forge lane and traffic](../../results/forge_lane_and_traffic.md)
