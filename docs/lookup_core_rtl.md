# SPARK-L: the lookup-only core (RTL sketch, verified in simulation)

Files: `hw/rtl/lookup/spark_lookup.v` (core), `tb_spark_lookup.v`, `run_check.py`; reference model `hw/system/lookup_ref.py`.
Why this core exists: `hw/results/matrix_free.md` shows a lookup-and-counter design comes within about 0.6 points (pooled, paired; 1.2 points if the network arbitrates) of the network hybrid on byte prediction, at about 57% of the memory. That is a small gap, not zero.
Labels: the behaviour below is SIMULATED (iverilog) and bit-exact against the reference; area and speed are ESTIMATED; nothing is synthesized to block RAM, placed, or timed.

## What it is

No matrices, no multipliers, no weights, no gradients. Per input byte it:
1. **learns**: for each of four hashed tables, the byte that just arrived is written against the context stored from the previous byte, using a 2-bit hysteresis counter (hit and same value: count up; hit and different value: count down, replace the value only at count 0; miss: install a new entry). This is a local, one-pass, in-place update.
2. **predicts**: the new 6-byte history is hashed four ways (contexts of 2, 3, 4 and 6 bytes); the highest-order table whose tag matches answers; otherwise it answers a space. It also reports which table answered and the entry's 2-bit count, as inputs for a confidence table.

Operations used: XOR, shifts, compares, two-bit counters, RAM reads and writes.
The hash is CRC-32 (reflected polynomial 0xEDB88320, start value = table number), which is XOR and shifts only. It matched zlib exactly in the testbench.

## Interface

`in_valid`, `in_byte[7:0]` (present a byte when `busy` is low) -> `out_valid` pulse with `pred[7:0]`, `hit`, `order_idx[1:0]` (0..3 = order 2, 3, 4, 6), `count[1:0]`. Parameter `TB` = log2 of entries per table (11 or 12 tested).

## Microarchitecture

```
in_byte -> [history 48b] -> 4 x CRC-32 (masked to 2,3,4,6 bytes) -> slot (top TB bits) + tag (12 bits)
                                   |                                      |
   stored (slot,tag) of previous ctx |                                      v
        --> read, learn (counter) --> write       4 x table RAM, 2^TB x 23 bits {valid, tag, value, count}
                                                  --> compare tags, choose highest hit --> pred, order, count
```

State machine, 5 cycles per byte (4 for the first byte after reset): IDLE (accept byte) -> URD (read the four stored-context entries) -> UWR (learn: combinational write on the same edge; shift the byte into the history) -> PRD (read the four new-context entries; remember their slot and tag) -> PCAP (compare tags, answer) -> IDLE.
After reset a sweep of 2^TB cycles zeroes every entry (silicon has no power-on contents), during which `busy` is high.

Bug found by the bit-exact check and fixed: the write port was first registered, so a write landed one cycle late and collided with the next state's read of the same slot (when a context repeats, e.g. indentation), giving about 2% wrong predictions. The write port is now combinational so the write lands on the edge that ends its state.

## Verification (SIMULATED)

`python hw/rtl/lookup/run_check.py <book dir>` drives the same bytes through the RTL (iverilog) and `lookup_ref.py` and compares pred, hit, order and count on every byte.
Result: 20,000 bytes of code and 20,000 bytes of prose, at TB = 11 and 12: **0 mismatches in 80,000 comparisons**. The reference model's code accuracy is 74.9% (TB 11) and 75.4% (TB 12), matching the sweep in `matrix_free.md`.
Table hit rate: 93.7-95.7%.
A separate hash unit test (three vectors) matches `zlib.crc32`.

## Cost estimate (ESTIMATED; yosys synth_gowin with the RAMs left as black boxes)

| | TB = 11 | TB = 12 |
|---|---|---|
| Table memory (4 x 2^TB x 23 bits) | 23.0 KB | 46.0 KB |
| Logic (LUT4 cells) | about 1,430 | about 1,440 |
| Wide-LUT mux cells | about 700 | about 670 |
| Flip-flops | about 180 | about 185 |

(The entry carries a valid bit, so 23 bits, not the 22 counted in earlier results.)
Speed at 27 MHz would be about 5.4 million bytes per second at 5 cycles per byte, against 4,190 cycles per byte for the v1 network (SIMULATED cycle counts); that is an estimate until timing is closed.
The four CRC units dominate the logic; a one-hash-unit sequential version would cut logic and add about 3 cycles per byte.

## Board facts from the outside review (second-hand; I have not opened the Gowin PDFs)

Two independent answers (GPT and Gemini, with source links to Sipeed's board page and Gowin DS226/UG285/SUG100/SUG282) agree on the Tang Nano 20K (GW2AR-18):
20,736 LUT4, 15,552 flip-flops, 46 block-RAM (BSRAM) blocks of 18 Kbit each (828 Kbit total), 2 PLLs, 27 MHz crystal. Block RAM geometries include 4096x4, 2048x9, 1024x18.
Both say the same about collisions: a semi-dual-port block RAM that reads and writes the same address in the same cycle returns an undefined value, and Gowin disallows it.
Not found by either: a design-specific maximum clock (BSRAM alone is rated up to 380 MHz, 230 MHz in read-before-write mode), the cost of a 48-bit CRC on this device, and a power report from the open-source flow. The vendor tool has a power analyzer (SUG282); the open-source flow (Apicula / nextpnr-himbaechel) reports timing and utilization.

## Block-RAM mapping check (yosys synth_gowin, no place-and-route)

Change made because of the collision warning: the RAM now has a read enable. Reads happen only in the two read states and writes only in the learn and clear states, so a read and a write never share a clock edge. The RAM is marked `ram_style = "block"` and `no_rw_check`, which is legitimate because the controller guarantees there is no collision. Bit-exact check after the change: still 0 mismatches in 80,000 comparisons.
Result of `synth_gowin` with the RAMs inferred (not black-boxed):

| | TB = 11 | TB = 12 |
|---|---|---|
| Block-RAM blocks used (4 tables) | 12 (DPX9) of 46 = 26% | 24 (DP) of 46 = 52% |
| LUT cells (LUT1-4) | about 1,420 of 20,736 (7%) | about 1,470 of 20,736 (7%) |
| Flip-flops | about 180 | about 185 |

This is the synthesizer's mapping only: not placed or routed (the open-source place-and-route tool is not installed in this container), so there is no timing result and no power result yet.
So by this check the design fits the board with room to spare; the real constraints (clock, routing) are unmeasured.

## What is missing

- Confidence: the core outputs order and count; a small lookup table from (order, count) to a confidence value is still to be added (the v2 confidence table design applies).
- No host interface or multi-stream state; the v1 UART wrapper pattern would apply.
- Timing closure and the ASIC memory macros are unchecked.
- Place-and-route, timing and power on the actual board are unchecked.
- The byte-level accuracy has not been confirmed on real-model drafting.
