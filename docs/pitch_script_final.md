---
title: Final pitch speaker script (23 Oct 2026)
date: 2026-10-23
tags: [pitch, script, qa]
---

# L: speaker script for the PALS innoWAH! pitch (embedded-systems club, 23 Oct 2026)

Deck: `L_pitch_final.pptx` (29 slides). Speaker: Navin (team L Lawliet, CKCET). Core talk about 9 minutes; a 5-minute cut is in section 6. Every number is said with its label: **measured**, **simulated** or **estimated**.

## 1. The one sentence

> "AI stops learning the day it ships. L is a small chip design that keeps learning on the device after it ships, without forgetting what it knew, using only counting: no multiplier, no matrix, no backpropagation. And I will show how real AI models can be altered, or newly designed, to run on it."

If you only get 20 seconds, say that, then: "Everything I show is simulation, one real GPU measurement, and design work. Nothing has run on a board yet, and I say exactly what that means."

## 2. The three questions every judge will ask, and your answers

Memorise these. They are slides 3, 16 and 21. How you tested it is slide 7.

**Q1. "What is wrong with the transformer and the GPU? Why change anything?"** (slide 3)
"Nothing is wrong with them for what they were built for: training and big batches in a data centre. Three things hurt on a device.
1. **The model is frozen.** It is trained once, then fixed. New data means retraining in a data centre, and a network trained on new things forgets old ones.
2. **Every token reads everything.** Making each word reads every weight, and attention keeps a memory that grows with the text. At one input at a time the chip waits for memory, not for maths.
3. **A GPU needs a crowd.** I measured it on my RTX 3050: one decision costs 69 millijoules alone and 1.95 in a batch of a thousand: 35 times worse when alone. A phone or a sensor decides one at a time.
The heat, cooling water and hardware turnover follow from that power. That is our motivation; I have not measured it."

**Q2. "Why should we agree with you and use your chip and model?"** (slide 16)
"For one specific job, I can show it is better: learning on the device, with a small memory, one input at a time. In staged learning on 59 thousand images the chip ends at 95.5% and a real CNN, which I ran on my own GPU, ends at 19.6% (chip simulated, CNN measured). It needs 84 KB and no multiplier, and about 74 times less energy per decision by operation count (estimated; the board run will measure it). The design matches the model bit for bit in 41 of 41 checks. **When everything is learned at once the CNN is still ahead, 99.1 to 97.9, and I say that. We do not replace the GPU: keep it for training and big models.**"

**Q3. "Can real AI models run on your chip?"** (slide 21)
"Three routes, and I will be exact about the status.
1. **Alter an existing model.** Ternary models, with weights of minus one, zero and plus one, turn multiplications into additions; published work runs language models of billions of parameters this way. That still has a matrix of additions, so it breaks our no-matrix rule, but it shows the multiplier is not needed.
2. **Design our own model.** A counting language model: hash the recent words into a sparse code, a table of counters predicts the next word one bit at a time. The counting classifier works in simulation; the language model is the next experiment.
3. **Grow the memory.** Big tables go in outside DRAM; only a few rows are touched per word, so bandwidth stays small. First we test, in simulation, whether quality grows with table size.
**We claim the route and the tests that can prove it wrong, not a billion-parameter result.** Today's chip is the small version of the idea."

If they push: "Is it proven at billions of parameters on your chip?" → "No. It is a hypothesis with falsification tests: it fails if quality drops at larger sizes without the matrix, if a fused GPU implementation gets within about 3 times, or if a transformer chip with the same memory matches it."

**Q4. "How did you test it? Did you run real AI models?"** (slide 7)
"Three ways. Standard tasks on an integer model of the chip, which is exactly its arithmetic: digits, clothing images, spoken digits and words, all at once, in stages, with noise, with two senses, with a new class from one example, with two chips merged; 3 to 5 seeds, a held-out speaker. A real CNN and a small network on the same data, the CNN on my own RTX 3050 so time and energy are measured. And the design itself: the Verilog matches the model bit for bit in 41 of 41 checks, the real-cell netlist matches, a formal equivalence check passed. **I did not run a language model or any large model on the chip. The models I ran are classifiers; the CNN is only the ruler. A board run is the next step.**"

## 3. How to pitch, and how not to

**Do**
- Order: problem (devices cannot learn), what is wrong with today's models, the idea, the proof and how it was tested, why use us, how bigger models can run, limits, ask.
- Say the label with every number. Judges trust the label more than the number.
- Say what is weaker before they find it (slide 23).
- Frame it as an **embedded system**: 84 KB, no multiplier, a small cheap FPGA, a UART interface, learning in the field.
- Slow down on: **95.5 against 19.6**, **84 KB**, **35 times worse at batch 1**, **41 of 41**.
- Not sure? "I have not measured that. Here is what I did measure."

**Do not**
- Do not say "replaces the GPU", "faster than a GPU" or "runs ChatGPT-size models". It does not, today.
- Do not say "never forgets". Say "keeps old classes far better than a normal network when learning in stages".
- Do not say "fabricated", "taped out", "tested on silicon", "runs on the Tang Nano".
- Do not call the energy number measured. The 74 times is an operation count; only the RTX 3050 numbers are measured.
- Do not say "we solved catastrophic forgetting". Say "greatly reduced, in our tests".
- Do not claim heat, water or e-waste savings as results. They are motivation.
- Do not read slides. One idea per slide.

## 4. What you can claim, and what you cannot

| You can say (with the label) | Source / label |
|---|---|
| Learning digits in 5 stages: chip about **95%**, a normal network about **19.5%** | SIMULATED chip |
| 59,063 digit images in stages: chip 95.5%, CNN 19.6%; all at once: CNN 99.09%, chip 97.91% | chip SIMULATED, CNN **MEASURED** on my RTX 3050 laptop GPU |
| One decision costs 69 mJ at batch 1 and 1.95 mJ at batch 1024 on my GPU (35 times) | **MEASURED** (NVML) |
| Memory for images **84 KB**, no multiplier; fits a Tang Nano 20K in place and route (89% logic, 0 multipliers) | design fact / SIMULATED place and route |
| RTL bit-exact with the model in **41 of 41** checks; core netlist in SKY130 cells matches the model; post-layout netlist proved equivalent to the synthesised one | SIMULATED |
| One digit decision: about 1,500 cycles, 55.7 µs at 27 MHz (FPGA build); about 320 cycles, 11.7 µs (pipelined option); GPU batch 1 about 1.8 ms | chip ESTIMATED from simulated cycles; GPU **MEASURED** |
| About 74 times less energy per decision than an 8-bit network, counting operations | ESTIMATED |
| Ternary language models of billions of parameters are published | published research; verify before quoting |
| A counting classifier works with counts only; a counting language model is our next experiment | SIMULATED / planned |
| Two chips merge by adding counters (91.4% on ten digits after one night, board-demo emulator); a new class from one example: digits 54 to 70, clothing 50 to 64 | SIMULATED |

| Do NOT claim | Why |
|---|---|
| It runs on hardware, a board or a chip | Not done; the board run is step 1 of the ask |
| It beats or replaces GPUs | Different job; a CNN is ahead when everything is learned at once |
| A billion-parameter model runs on L | A hypothesis; tests not yet run |
| Measured chip power or energy | Only an estimate until the board is read |
| "Never forgets" / "solved forgetting" | A rotated-digits test dropped old digits from 95 to 45% without the frozen-memory option |
| "First chip that learns continuously" | Hyperdimensional-computing accelerators and Loihi 2 exist; what is new is the combination |
| Heat, water, e-waste savings | Motivation, not measured |
| Large vocabularies, real audio-visual data, real noise | Small tests only |

## 5. The script, slide by slide (29 slides)

Times are for the 9-minute talk. Say the bold sentence even if you skip the rest.

**1. Cover (0:15).** "We are L Lawliet from CKCET and the project is called L. **Every number is labelled simulated, estimated or measured, and nothing has run on a real board yet.**"

**2. AI stops learning the day it ships (0:35).** "A phone, a camera, a sensor node: the AI inside was trained once on a big machine. If the world changes, it does not learn. **I want the device itself to learn, without forgetting.**"

**3. What today's model and GPU get wrong (0:60).** Answer Q1 above, three points, then: "**Heat, water and hardware turnover follow from the power: that is our motivation, not a result.**"

**4. The idea: a brain, as a chip (0:40).** "A brain counts, compares and sleeps. L does the same: a table of small counters decides, and at night the chip dreams about old classes from its own counters, so new learning does not overwrite them. **No multiplier, no matrix, no backpropagation.**"

**5. Learns in stages and keeps what it knew (0:45).** "Five stages, two digits at a time. A normal network ends near 19.5%, because it forgets. Our chip ends near 95% (simulated). **On 59,000 images a real CNN on my GPU ended at 19.6% in stages and the chip at 95.5%.**"

**6. Close to a CNN trained on everything (0:35).** "When everything is learned at once the CNN wins, and I say so: 99.09 against 97.91 on digits, about 2 to 3 points on clothing. **Close, without any multiplier.**"

**7. How we tested it (0:45).** "Three ways. One: standard tasks on an integer model of the chip, which is exactly the arithmetic it does: handwritten digits, clothing images, spoken digits and words; all at once, in stages, with noise, with two senses, a new class from one example, two chips merged; 3 to 5 seeds and a held-out speaker. Two: a CNN and a small network trained on the same data, with the CNN run on my own RTX 3050 so accuracy, time and energy are real. Three: the Verilog matches the Python model bit for bit in 41 of 41 checks, the real-cell netlist matches, and a formal equivalence check passed. **What we did not test: a language model or any large model on the chip, a board run, real-world noise. The models we ran are classifiers; the CNN is only our ruler.**"

**8 to 12. Scale, sound, two senses, new class, sharing (1:15 total; pick two).** "It still works at 60,000 images with one rule that sets its sleep interval. It hears spoken words and noise hurts less (simulated). Two senses help each other. A new class from one example after shipping. Two chips merge by adding counters: a normal network cannot do that."

**13. The design in one picture (0:45).** "Camera and microphone, a retina and a cochlea that make on-off bits, a sparse code, the fast table that decides, the dream memory, the slow table, a day-night sequencer, and a UART. **Counts, compares, shifts, table lookups. That is all.**"

**14. Small, cheap, no multiplier (0:35).** "84 KB. It fits a 25-dollar Tang Nano 20K with zero multipliers (simulated place and route). About 74 times less energy than an 8-bit network, counting operations. **That 74 times is an estimate; I will measure it on the board.**"

**15. Chip design against a real GPU (0:55).** "Same decision on my RTX 3050. Measured: about 1.8 milliseconds and 69 millijoules at batch one; 22,000 decisions a second at batch 1024. The chip design needs about 1,500 cycles per decision: 56 microseconds at 27 megahertz, 12 in the pipelined option. **Chip times are estimates from simulated cycles, not a board run. The GPU wins when it can batch.**"

**16. Why use L instead, for this job (0:50).** Answer Q2 above. End on the green box: "**Use L when the job is learning on the device, with a small memory, one input at a time. Keep the GPU for training and big models.**"

**17. Why this is an embedded system (0:35).** "Tight memory, no multiplier, a small FPGA, a camera-style input and a UART. It learns in the field, sleeps when idle, and its memory can be moved between devices."

**18. Verified bit for bit (0:30).** "41 of 41 checks: the RTL matches the Python model exactly, and the layout flow in the open tool chain reaches routing with zero violations by the router's own count. **That is a layout in simulation, not a fabricated chip.**"

**19. The design, so you can verify it (0:15).** "Everything is in a public repository: the model, the RTL, the checks."

**20. What L solves, and what it does not (0:30).** "It solves a small continual learner for sensors. It does not run existing models as they are, and it is not a GPU."

**21. How real AI models can run on L (0:70).** Answer Q3 above, three routes. End on: "**We claim the route and the tests that can prove it wrong, not a billion-parameter result.**"

**22. The hypothesis we will test (0:30).** "A brain-style model with constant-size state and sparse activity, on a chip built for it, needs less memory traffic and energy per token than a transformer on a GPU at the same quality. It is a hypothesis. It fails if quality drops at larger sizes, if a fused GPU implementation gets within about 3 times, or if a transformer chip with the same memory matches it."

**23. Where it is level, and where it is weaker (0:50, do not skip).** "Level: digits and short spoken-word tests against a CNN. Weaker: clothing in stages is about 82%, five points under its one-pass number; a trained CNN is about two points ahead on clothing. Tests are small, noise is simulated, the two-sense data is paired by class. **A few steps still run on the host.**"

**24. Not the first (0:25).** "Hyperdimensional-computing accelerators and Intel Loihi 2 exist. What is new is the combination: dreams drawn from small counters, no multiplier, merging by adding counts."

**25 to 27. What comes next, two tracks, silicon plan (0:40 total).** "Next is the board run. The second track is the model-running chip for the bigger problem. We write the design independent of the node. A 5-nanometre-class chip costs tens of millions of dollars and we do not claim it."

**28. What we need to go further (0:50).** "Step 1: a Tang Nano 20K, about 4,200 rupees, for the first measured numbers. Pass: bit-exact with simulation, accuracy and power measured. Step 2: a micro-chip on a shared shuttle, about 100 to 300 dollars a tile. Step 3: a mature-node chip through a university or programme partner. **Today I ask for step 1, and for a mentor or partner for step 2.**"

**29. Close (0:15).** "AI that keeps learning, on the device, with counting, and a clear route to bigger models, with tests that can prove us wrong. Thank you."


## 6. The 5-minute cut
Slides 1, 2, 3, 4, 5, 6, 7, 13, 15, 16, 21, 23, 28, 29. Say the bold sentences only. Skip 8 to 12, 14, 17 to 20, 22, 24 to 27.

## 7. More hard questions, short answers

- **Has it run on hardware?** "No. The RTL is bit-exact with the model and fits the Tang Nano in place and route (simulated). The board run is step 1 of my ask."
- **Does it match a neural network?** "Close, not equal: 97.9 against 99.1 on digits when everything is learned at once. In stages it is far ahead, because a normal network forgets (95.5 against 19.6)."
- **Why not fine-tune a transformer on the device?** "Fine-tuning needs gradients and a lot of memory, and a fine-tuned network forgets. L learns by counting, in place, with dreams that protect old knowledge."
- **Why not just use a bigger GPU?** "For training and big models, you should. L is for a device that must learn after shipping within a tiny power and memory budget, with no server."
- **Is the energy number real?** "The 74 times is an operation count, an estimate. The GPU numbers are measured. The chip's energy gets measured on the board."
- **Is a counting language model any good?** "It will start at roughly n-gram quality, which is weaker than a transformer. The experiment is to see whether dreams and richer codes close the gap, and whether quality grows with memory."
- **What are dreams?** "While idle, the chip draws pretend examples of old classes from its own counters and learns them again, so new learning does not overwrite old knowledge. It stops by itself when surprises become rare."
- **Is this like a real brain?** "Brain-inspired, not brain-identical. Local counting, sleep and replay are brain-like; the sense layer and the dream sampler are engineered."
- **Where did it fail?** "Staged clothing at scale, about 82%. Cheap fixes failed. A multi-prototype option helps by about 3 points but costs memory and is not in the RTL yet."
- **What will you do with money or time?** "Board run first. Then the counting language model experiment, better dreams for clothing, a write-up and a demo video."
- **Is the data realistic?** "Standard digit and clothing sets and a small spoken-word set. Larger vocabularies and real noise are not tested."

## 8. Before you go on stage

- Open the deck at slide 1; check slides 3, 7, 15, 16, 21 and 28 render.
- Know the numbers cold: **95.5 against 19.6**, **35 times worse at batch 1**, **84 KB**, **41 of 41**.
- If a slide runs long, drop slides 8 to 12 first.

Related: [Pitch Q&A sheet](pitch_qa_sheet.md), [Cortex pitch script (earlier)](pitch_script_cortex.md), [Results at a glance](results_at_a_glance.md), [L hypothesis](L_hypothesis.md), [Index](INDEX.md)
