# SPARK core — synthesis and place-and-route (target: Tang Nano 20K, Gowin GW2AR-18)

Tools: Yosys 0.33 (`synth_gowin`), nextpnr-himbaechel (built from source, GW2A-18C chip database from Apycula), `gowin_pack`.

## History of fitting the design
| Build | Lanes | Block RAM (of 46) | LUT4 after place-and-route (of 20,736) | Result |
|---|---|---|---|---|
| 1. Weights as read-only memories | 16 | 0 (weights became logic) | — (~63.7k LUT cells at synthesis) | ✘ ~3× over |
| 2. Weight load port + block-RAM hints | 16 | 29 | — (~31.5k at synthesis) | ✘ |
| 3. + neuron constants fixed at build time | 16 | 29 | — (~24.4k at synthesis) | ✘ |
| 4. + 16-bit accumulators, 4-lane post pass, single-port recall table | 16 | 29 | 19,743 (95%) | ✘ placement failed (too full) |
| **5. Lane count parameterised, built with 8 lanes** | **8** | **29 (63%)** | **13,812 (66%)** | **✔ placed, routed, timing met** |

## Final build (board top with UART, `hw/board/spark_board_top.v`)
- LUT4: 13,812 / 20,736 (66%) · flip-flops: 3,899 / 15,552 (25%) · LUT-RAM (RAM16SDP4): 304 / 648 (46%) · block RAM: 29 / 46 (63%)
- **Maximum clock: 54.4 MHz** (core clock domain) → **passes at the board's 27 MHz** with ~2× margin.
- Bitstream: `hw/pnr/spark_tangnano20k.fs.gz` (gunzip before flashing). Contains the random demo weights.

## Cautions before flashing
- Pin numbers in `hw/board/tangnano20k.cst` are marked TODO (unverified against the Sipeed schematic); check them first. Wrong pins cannot damage the FPGA in most cases but the design will not respond.
- Button S1 polarity is assumed active-high; if the heartbeat LED does not blink, invert it.
- Every reported speed (tokens/s) is still MODELLED until measured on the board.
