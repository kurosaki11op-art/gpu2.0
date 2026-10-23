---
title: What limits GPUs for AI, and what L does about each (24 Oct 2026)
tags: [l, gpu, power, water, e-waste, design]
---

# GPU limits against the L design (ESTIMATED; public figures are recalled from memory and must be checked before any external use)

**Rule used here:** a limit is listed with its cause; "what L has shown" holds only things in this repo with their labels; "not shown" is everything else. L is a different kind of model (counts and lookups), so a limit it avoids on its own workload is not automatically avoided for a transformer.

## 1. The limits

| # | GPU limit | Cause | Rough public size (verify) | What L does | Shown in this repo | NOT shown |
|---|---|---|---|---|---|---|
| 1 | **Memory wall / data movement** | weights live in off-chip HBM/DRAM and are fetched for every token; a DRAM access costs about 100x an on-chip SRAM access and about 10,000x an 8-bit add (Horowitz, ISSCC 2014, 45 nm: DRAM 32-bit read ~640 pJ, 8 KB SRAM ~5 pJ, 8-bit add ~0.03 pJ) | H100: 80 GB HBM, ~3.35 TB/s; a large share of inference energy is moving weights | all state in on-chip SRAM (Cerebras idea); read only the rows that are active | sparse reads: 210 to 570 active rows of ~4,600 per image (SIMULATED); wafer sizing for 8 MB to 44 GB (ESTIMATED) | a real SRAM macro at the target node; weights of a transformer in SRAM |
| 2 | **High computation (dense multiply-add)** | every weight multiplies every activation | tens of TFLOPs sustained for LLM inference | no multiplier, no matrix: add the rows of active bits | exact RTL; decision = adds only; ESP32 firmware logic check (0 of 200 differ) | quality on language tasks beyond n-gram level (counting LM 1.67 bits per char at 8 MB vs 2.1 for a small neural model at <0.5 MB) |
| 3 | **Power** | multiply-add array + HBM + cooling | H100 700 W, B200 about 1,000 W, 8-GPU server about 10 kW | energy per image is bytes touched, not weights stored | picture to answer about 42 uJ (layout ESTIMATE) vs GPU 0.29 to 69 mJ (MEASURED on a laptop GPU): about 7 to 1,650x | board or silicon measurement; the encoder is 99% of chip energy today |
| 4 | **Heat** | all power ends as heat in one package; liquid cooling is now required for the newest racks | 100 kW class racks | lower power per answer; sparse activity (clock-gated banks) | gated-clock layout power (ESTIMATED); measured switching from simulation (Level 3) | thermal behaviour of a wafer-size part (Cerebras itself needs ~23 kW per system with custom cooling) |
| 5 | **Water** | evaporative cooling of the data centre plus water for the power plant | studies estimate hundreds of thousands of litres to train one large model and about half a litre per 10 to 50 queries (Li et al. 2023) | water follows energy: less energy per answer, proportionally less cooling water | nothing measured; only the energy ratio above | any water figure of our own: **no measurement or model exists, a ratio of energy is the only claim** |
| 6 | **E-waste and embodied carbon** | frequent replacement (2 to 4 years) of accelerators; manufacturing at advanced nodes is itself carbon and water heavy | one study projects 1.2 to 5 million tonnes of cumulative AI e-waste 2020 to 2030 (Wang et al., Nature Computational Science 2024) | **learn on the fly, no retraining rounds**: a deployed L chip changes by writing counters, not by new hardware; a mature node (130 nm) lasts longer; SRAM-only, no HBM stack to discard | design argument only | lifetime or yield data; a mature-node chip is bigger per unit of work, which costs silicon area |
| 7 | **Training cost and forgetting** | backprop over the whole data set; new data forces retraining or fine-tuning that forgets | days to months on thousands of GPUs | learning by counting, one pass, no backprop, dreams hold old classes | staged learning: L Cortex 81.4% (clothing) / 94.2% (digits) vs MLP/CNN ~20% after the same five stages (SIMULATED) | staged learning of language; the MLP result used no replay or regularisation |
| 8 | **Supply, cost, access** | HBM and advanced packaging capacity, export limits | multi-year waitlists for the top parts | open process (SKY130) and a tile that any memory compiler can fill | tile RTL, synthesis and partial routing; board prep | any fabricated silicon |

## 2. Where L loses, stated plainly

- **Quality.** On clothing a 4-bit MLP at equal memory beats L Cortex (89.5% vs 85.7%); on text a small neural model beats the counting model below about 0.5 MB. L's advantage today is staged learning, energy per decision and a lookup-only chip, **not** accuracy per byte.
- **Confusable classes.** Shirt is recognised 63% of the time, confused with T-shirt (see `hw/results/clothing_confusion.md`). A model should not stay confused on such pairs; work on this is in `hw/results/shirt_specialist.md` when the experiment finishes.
- **Scope.** Nothing here shows an L model matching a transformer. The wafer machine is a plan; sizing numbers are ESTIMATED.
- **Rebound.** Cheaper answers can raise total use (Jevons effect); a per-answer saving is not a total saving.

## 3. Design consequences (the order of work)

1. Fix L's weak spots first (confusable classes, staged loss on similar pairs, encoder energy).
2. Replace HBM-style assumptions by on-chip SRAM everywhere: tile = router + bank + core, memory behind one wrapper (`sram_wrap.v`), so a foundry compiler or denser memory is a one-module change.
3. Measure before claiming: ESP32 (logic, speed, power of the MCU baseline), Tang Nano 20K (FPGA tile), then silicon; fabrication last.

Related: [Wafer design](L_wafer_design.md), [Project memory](PROJECT_MEMORY.md), [End to end power](../hw/results/end_to_end_power.md), [Clothing confusion](../hw/results/clothing_confusion.md), [Journal](journal.md)
