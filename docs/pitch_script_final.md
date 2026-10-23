---
title: Final pitch speaker script (23 Oct 2026)
date: 2026-10-23
tags: [pitch, script, qa]
---

# L: speaker script for the PALS innoWAH! pitch (embedded-systems club, 23 Oct 2026)

Deck: `L_pitch_final.pptx` (25 slides). Speaker: Navin (team L Lawliet, CKCET). Core talk about 8 minutes; a 5-minute cut is at the end. Every number is said with its label: **measured**, **simulated** or **estimated**.

## 1. The one sentence

> "AI stops learning the day it ships. L is a small chip design that keeps learning on the device after it ships, without forgetting what it already knew, using only counting: no multiplier, no matrix, no backpropagation."

If you only get 20 seconds, say that, then: "Everything I show today is simulation, one real GPU measurement, and design work. Nothing has run on a board yet, and I will say exactly what that means."

## 2. How to pitch, and how not to

**Do**
- Start with the problem (devices cannot learn after shipping), then the idea (a brain-like counting chip), then the proof, then the limits, then the ask. In that order.
- Say the label with every number. Judges trust the label more than the number.
- Say what is weaker before they find it. The weak-spots slide is a strength: it shows you know your own work.
- Frame it as an **embedded system**: tight memory (84 KB for images), no multiplier, a small cheap FPGA, a UART interface to any microcontroller, learning in the field.
- Slow down on the three numbers that matter: staged learning (95% against 19.5%), the gap to a CNN (about 1 point on digits, about 2 to 3 on clothing), and the 84 KB memory.
- When asked something you do not know: "I have not measured that. Here is what I did measure."

**Do not**
- Do not say "replaces the GPU" or "faster than a GPU". It does not run existing models and it is not a GPU alternative for training. It is a small continual learner for sensors.
- Do not say "never forgets". Say "keeps old classes far better than a normal network when learning in stages".
- Do not say "fabricated", "taped out", "tested on silicon" or "runs on the Tang Nano". None of these is true yet.
- Do not call the energy number measured. The 9.4 nJ is an operation count (estimated). The only measured numbers are from the RTX 3050 run.
- Do not claim it beats a trained CNN. It is close, not ahead, when everything is learned at once.
- Do not read slides. One idea per slide, then move on.
- Do not mention open engineering items you cannot finish answering in the time. If asked about them, say: "That is part of the next milestone."

## 3. What you can claim, and what you cannot

| You can say (with the label) | Source / label |
|---|---|
| Learning digits in 5 stages: about **95%**, a normal network about **19.5%** | SIMULATED chip; network trained on the same data |
| On 59,063 digit images in stages: chip 95.5%, CNN 19.6% | chip SIMULATED (integer model), CNN **MEASURED** on my RTX 3050 laptop GPU |
| All at once: CNN 99.09%, chip 97.91% (59k images) | same split of labels |
| Memory for images: **84 KB**, no multiplier | design fact |
| Fits a Tang Nano 20K in place and route: 89% logic, all 46 block RAMs, 0 multipliers | SIMULATED place and route |
| RTL is bit-exact with the model in **41 of 41** checks | SIMULATED (RTL simulation) |
| The core netlist in real SKY130 cells matches the model (small core, 0 mismatches; flip-flops powering up 0 and 1) | SIMULATED gate-level |
| Post-layout netlist proved logically equivalent to the synthesised one (77,330 points) | SIMULATED, formal |
| One digit decision: chip 55.7 µs (FPGA build) or 11.7 µs (pipelined option) at 27 MHz; GPU batch 1 about 1.8 ms | chip time ESTIMATED from simulated cycles; GPU **MEASURED** |
| Energy: about 74 times less than an 8-bit network, counting only the operations a decision needs | ESTIMATED |
| GPU measured energy per decision: 69 mJ (batch 1), 1.95 mJ (batch 1024) | **MEASURED** (NVML, my laptop GPU) |
| Two chips can share knowledge by adding counters (91.4% on all ten digits after one night, board-demo emulator) | SIMULATED |
| A new class from one example, after shipping: digits 54 to 70, clothing 50 to 64 | SIMULATED |

| Do NOT claim | Why |
|---|---|
| It runs on hardware, a board or a chip | Not done. The board run is step 1 of the ask. |
| It beats or replaces GPUs | Different job; the CNN is ahead when everything is learned at once. |
| Measured chip power or energy | Only an estimate until the board is read. |
| "Never forgets" | A rotated-digits test dropped old digits from 95 to 45% without the frozen-memory option. |
| "First chip that learns continuously" | Hyperdimensional-computing accelerators and Loihi 2 exist. What is new is the combination (dreams from counters, no multiplier, merge by adding). |
| Large vocabularies, real audio-visual data, real noise | Small tests only (10 to 35 spoken words, paired sets, simulated noise). |
| Anything about a GPU-class (5 nm) chip | Needs tens of millions of dollars; say so. |

## 4. The script, slide by slide

Times are for the 8-minute talk. Say the bold sentence even if you skip the rest.

**1. Cover (0:15).** "Hello. We are L Lawliet from CKCET and the project is called L. **Every number I show is labelled simulated, estimated or measured, and nothing has run on a real board yet.**"

**2. AI stops learning the day it ships (0:40).** "A phone, a camera, a sensor node: the AI inside was trained once, on a big machine. If the world changes, it does not learn. To teach it something new you retrain in a data centre and send an update. **I want the device itself to learn, without forgetting.**" (Judges are embedded people: this is their pain.)

**3. The idea: a brain, as a chip (0:40).** "A brain does not do matrix maths. It counts, it compares, and it sleeps. When idle it replays old experiences. L does the same: a table of small counters decides, and at night the chip dreams about old classes from its own counters, so new learning does not overwrite them. **No multiplier, no matrix, no backpropagation.**"

**4. Learns in stages and keeps what it knew (0:50).** "Five stages, two digits at a time. A normal network ends near 19.5%, because it forgets. Our chip ends near 95% (simulated). **On 59,000 images I also ran a real CNN on my laptop GPU: it ended at 19.6% in stages, the chip at 95.5%.**"

**5. Close to a CNN trained on everything (0:40).** "When everything is learned at once, the CNN wins, and I say so: 99.09 against 97.91 on digits, about 2 to 3 points on clothing. **The chip is close without any multiplier.**"

**6 to 10. Scale, sound, two senses, new class, sharing (1:30 total; pick two).** Say only: "It still works at 60,000 images with one rule that sets its sleep interval. It hears spoken words and noise hurts less (simulated). Two senses help each other. A new class from one example after shipping. And two chips merge by adding counters: a normal network cannot do that." (Skip slides you are short on.)

**11. The design in one picture (0:50).** Point along the picture: "Camera and microphone, a retina and a cochlea that make on-off bits, a sparse code, the fast table that decides, the dream memory, the slow table, a day-night sequencer, and a UART to any microcontroller. **Counts, compares, shifts, table lookups. That is all.**"

**12. Small, cheap, no multiplier (0:40).** "84 KB for images. It fits a 25-dollar Tang Nano 20K with zero multipliers (simulated place and route). About 74 times less energy than an 8-bit network, counting only the operations a decision needs. **That 74 times is an estimate. I will measure it on the board.**"

**13. Chip design against a real GPU (0:60).** "I ran the same decision on my RTX 3050 laptop GPU. Measured: batch one takes about 1.8 milliseconds and 69 millijoules; at batch 1024 it reaches 22,000 decisions per second. The chip design needs about 1,500 cycles per decision, which is 56 microseconds at 27 megahertz in the FPGA build, and about 320 cycles, 12 microseconds, in the pipelined option. **Those chip times are estimates from simulated cycles, not a board run. The GPU wins when it can batch; a CNN is more accurate when everything is learned at once. Our case is learning on the device, in stages, at a tiny energy budget.**"

**14. Why this is an embedded system (0:40).** "Tight memory, no multiplier, a small low-cost FPGA, a camera-style input and a UART. It learns in the field, sleeps when idle, and its memory can be moved between devices."

**15. Verified bit for bit (0:30).** "41 of 41 checks: the RTL matches the Python model exactly, and the layout flow in the open tool chain reaches the routing stage with zero violations by the router's own count. **That is a layout in simulation, not a fabricated chip.**"

**16 to 18. The design to verify, what it solves, the hypothesis (0:40).** "What it solves: a small continual learner for sensors. What it does not: it does not run existing models and it is not a GPU. Our hypothesis for the bigger problem, a counting accelerator for language models, is a hypothesis; we will test it."

**19. Where it is level and where it is weaker (0:50, do not skip).** "Level: digits, and short spoken-word tests against a CNN. Weaker: clothing in stages is about 82%, five points under its one-pass number, and I tried many fixes. A trained CNN is still about two points ahead on clothing. Tests are small, the noise is simulated, the two-sense data is paired by class. **A few steps still run on the host.**"

**20. Not the first (0:30).** "Hyperdimensional-computing accelerators and Intel Loihi 2 exist. What is new is the combination: dreams drawn from small counters, no multiplier, and merging by adding counts."

**21 to 23. What comes next, two tracks, silicon plan (0:40 total).** "Next is the board run. We write the design independent of the node. A 5-nanometre-class chip costs tens of millions of dollars and we do not claim it."

**24. What we need to go further (0:50).** "Step 1: a Tang Nano 20K, about 4,200 rupees, for the first measured numbers. Pass: bit-exact with simulation, accuracy and power measured. Step 2: a micro-chip on a shared shuttle, about 100 to 300 dollars a tile, to show the verified units in silicon. Step 3: a mature-node chip through a university or programme partner. **Today I am asking for step 1, and for a mentor or a partner for step 2.**"

**25. Close (0:15).** "AI that keeps learning, on the device, with counting. Thank you. Happy to show the table, the numbers and the code."

## 5. The 5-minute cut

Slides 1, 2, 3, 4, 5, 11, 12, 13, 19, 24, 25. Say the bold sentences only. Skip 6 to 10, 14 to 18, 20 to 23.

## 6. Short answers to likely questions

- **Has it run on hardware?** "No. The RTL is bit-exact with the model and fits the Tang Nano in place and route (simulated). The board run is step 1 of my ask and gives the first measured numbers."
- **Does it match a neural network?** "Close, not equal: 97.9 against 99.1 on digits at 59k images when everything is learned at once. In stages it is far ahead, because a normal network forgets (95.5 against 19.6, the CNN measured on my GPU)."
- **Why not just use a GPU?** "A GPU wins on throughput when it can batch and for training. L is for a device that has to learn after shipping, in a tiny power and memory budget, with no server."
- **Is that energy number real?** "The 74 times is an operation count, an estimate. The GPU numbers are measured. The chip's energy gets measured on the board."
- **What are dreams?** "While idle, the chip draws pretend examples of old classes from its own counters and learns them again, so new learning does not overwrite old knowledge. It stops by itself when surprises become rare."
- **Is this like a real brain?** "Brain-inspired, not brain-identical. Local counting rules, sleep and replay are brain-like; the sense layer and the dream sampler are engineered."
- **Where did it fail?** "Staged clothing at scale, about 82%. Cheap fixes (more daydreams, margins, structured dreams) failed. A multi-prototype option helps by about 3 points but costs memory and is not in the RTL yet."
- **What will you do with money or time?** "Board run first. Then learned word features and better dreams for clothing, a write-up and a demo video."
- **Is the data realistic?** "Standard digit and clothing sets and a small spoken-word set. Larger vocabularies and real noise are not tested."

## 7. Before you go on stage

- Open the deck at slide 1; check slides 11, 13, 15 and 24 render.
- Have `docs/results_at_a_glance.md` open as your number sheet.
- Know the three numbers cold: **95 against 19.5**, **84 KB**, **41 of 41**.
- If a slide runs long, drop slides 6 to 10 first.

Related: [Pitch Q&A sheet](pitch_qa_sheet.md), [Cortex pitch script (earlier)](pitch_script_cortex.md), [Results at a glance](results_at_a_glance.md), [Index](INDEX.md)
