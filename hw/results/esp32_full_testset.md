---
title: The whole 10,000-image test set on a real ESP32, with a hardware cascade (31 Oct 2026)
tags: [spark, esp32, measured, cascade, bit-exact]
---

# Full test set on a real ESP32 (31 Oct 2026)

The founder flashed `hw/mcu/esp32_serve` (version 3 of the L algorithm as an image server, ESP32 Dev Module on COM7, 240 MHz, 921,600 baud) and ran `hw/mcu/serve_host.py --port COM7` from a Windows laptop: all 10,000 Fashion-MNIST test images were sent one at a time, classified on the board, and the answers compared with the reference model. The first 2,000 images (no labels used) set the reject threshold for 15% flagged from the margins the board itself returned; the remaining 8,000 are the evaluation images; flagged images were answered by the host from the stored logits of the strong reference CNN (the fallback). Figures below are transcribed from the founder's screenshot of the printed results (the JSON file stayed on the founder's machine). **MEASURED on the ESP32 (software, not the chip), except that the fallback's logits are stored from an earlier run and the energy is not measured.**

| | result |
|---|---|
| **identical to the reference model on every image** (prediction, routed bit, margin) | **YES, 0 of 10,000 mismatching** |
| accuracy of the L algorithm on the ESP32 | 89.73% on all 10,000; 89.59% on the 8,000 evaluation images |
| routed to L Deep | 20.0% |
| reject threshold (15% quantile of the board's margins on 2,000 unlabelled images) | 2,889 (the same value the model gave in the [cascade demo](cascade_demo.md)) |
| flagged share of the evaluation images | 16.3% |
| accuracy on the answered (unflagged) images | 95.09% |
| **cascade: the ESP32 answers, the fallback takes the flagged ones** | **91.24%**; the fallback alone 91.53% |
| time on the board | 9.09 ms per image of computation; 18.2 ms per image wall time including the serial transfer; 182 s for the 10,000 |

Reading: (1) the bit-exactness that the RTL checks showed in simulation now also holds in real hardware over the whole test set, which confirms the C port, the encoder, both tables and the reject flag; (2) the accuracy, the flagged share, the 95.09% on the answered images and the 91.24% cascade equal the figures of the model's cascade demo to the digit; (3) this is the first end-to-end hardware cascade: a device answers the sure images and hands the unsure ones to a stronger fallback. Not shown: the energy of any of it (the USB meter is still to come), and the custom chip's speed or energy. The ESP32 is a stand-in processor for the algorithm, not the chip.

Related: [First ESP32 run](esp32_first_run.md), [Cascade demo](cascade_demo.md), [MCU port](mcu_port.md), [hw/mcu README](../mcu/README.md), [Results index](INDEX.md)
