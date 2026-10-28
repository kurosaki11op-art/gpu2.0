---
title: FPGA board decision for the three-layer pitch build (28 Oct 2026)
tags: [spark, fpga, decision, plan, hardware]
---

# FPGA board decision (28 Oct 2026)

Founder's go-ahead to decide the board. This note records the decision, the three checks to make before paying, a fallback, and what is ready for bring-up. Prices and specifications come from search results (secondary, partly 2023) and must be re-checked at purchase. The decision is for the small pitch design only (about 1.3 Mbit of memory); the 2 GB, 5 nm design is not an FPGA project.

## What the design needs (from the virtual device synthesis, Gowin family counts)

74 block RAMs of 18 Kbit (about 1.3 Mbit), 16 multipliers of 9 x 9, about 6,000 logic cells (4,861 LUT4 plus 1,134 carry cells), 779 flip-flops, one UART. Headroom wanted: at least 2 Mbit of block RAM and room for the four-engine Deep core (76 block RAMs).

## Decision

**Primary: a Sipeed Tang Mega 138K (the Dock, or the Pro Dock if the price difference is small).** Its GW5AST-138 chip has about 6,120 Kbit of block SRAM (340 blocks), 298 multipliers and 138K logic cells ([CNX Software](https://www.cnx-software.com/2023/10/01/sipeed-tang-mega-138k-pro-dock-features-gowin-gw5ast-fpga-risc-v-soc/)): the design would use about 22% of its block RAM, 5% of its multipliers and 4% of its logic, with room for everything else. It is the same Gowin family our synthesis counts come from, and it is the family of the founder's Tang Nano 20K. A plain 138K Dock is described as the lower-cost board with the same GW5AST chip ([CNX Software, 2024](https://www.cnx-software.com/2024/06/28/sipeed-tang-mega-138k-dock-is-a-lower-cost-gowin-gw5ast-fpga-risc-v-development-board/)); we need only a UART and power, not the Pro's extras. An Indian reseller lists both the [138K Dock](https://probots.co.in/sipeed-tang-mega-138k-dock-gw5ast-fpga-riscv-board.html) and the [Pro Dock](https://probots.co.in/sipeed-tang-mega-138k-pro-dock-gw5ast-fpga.html); I found no price or stock.

**Fallback: Digilent Arty A7-100T** (4,860 Kbit block RAM, 240 DSP slices; [Digilent](https://digilent.com/shop/arty-a7-artix-7-fpga-development-board/), $258 to 314 in the search) with the Xilinx Vivado toolchain, the most widely used, if the Gowin toolchain check below fails.

## Three checks before paying (do not skip)

1. **Toolchain licence.** Gowin's free [Educational EDA](https://manilatimes.net/2024/11/30/tmt-newswire/globenewswire/gowin-semiconductor-introduces-educational-eda-version-v191003-with-mac-os-support/2013457) exists, but an older guide says it supports fewer devices, and I could not confirm that the GW5AST-138 is on its list. Install the current Educational EDA and look at the device list, or ask Gowin or Sipeed for a licence, before buying. If the chip needs a paid licence, take the Arty A7-100T.
2. **Package and pins.** The Pro Dock's chip is reported as GW5AST-LV138FPG676A and the plain Dock's as GW5AST-LV138PG484A (a conflict between Sipeed pages): the constraint file must match the board bought. UART, clock and LED pins must be read from the board's schematic or example project; I found none and have not guessed any.
3. **Price and stock in India**, including shipping and duty, against the Rs 1 lakh budget (the board is a small part of it; the rest should buy a USB power meter and spares).

## Bring-up plan once the board is in hand

1. Synthesise the board top (`hw/rtl/top/l_board_top.v`, parameters CLK_HZ and BAUD set to the board's clock and 115200) in the vendor tool with the pin file; check utilisation against the counts here.
2. Run the host protocol ([l_host.py](../hw/board/l_host.py)): one recognition, then the matrix product; compare with the virtual device results ([virtual device tests](../hw/results/virtual_device_tests.md)).
3. Run the 10,000-image test through the UART link (slow: about 800 bytes per image, so use a few hundred images) and compare accuracy and cycle counts with the simulation.
4. Measure power with an inline USB meter and then [the measurement protocol](measurement_protocol.md); run the GPU baseline on the founder's PC.

## Ready now

`hw/board/fpga_bringup/README.md` lists the files to bring and a constraint-file template with the pins left blank on purpose. The RTL, the host script and the golden test data are in the repository.

Related: [Measurement protocol](measurement_protocol.md), [Status, 28 Oct 2026](L_status_28oct.md), [Virtual device tests](../hw/results/virtual_device_tests.md), [Docs index](INDEX.md), [Journal](journal.md)
