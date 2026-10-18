---
title: SPARK Cortex pitch script (23 Oct event)
date: 2026-10-19
tags: [pitch, script, cortex]
---
# SPARK Cortex: speaking script for the 23 October event

Deck: [SPARK_Cortex_pitch.pptx](SPARK_Cortex_pitch.pptx) (14 slides, same notes inside the file). About 8 minutes at a calm pace, 40 to 60 seconds per slide.
Cut list if time is short: drop slides 7, 8, 10 and 12 (sharing, diagnosis, verification, prior art) and keep the rest (about 5 minutes).
Rules while speaking: say the label (simulated, estimated) with every number; say "nothing is measured on hardware yet" once near the start and once at the limits slide; never say "first", "never forgets", "better than a network" or "replaces GPUs" (see [claims sheet](cortex_claims_sheet.md)).

## Slide 1: Cover

Hello judges. We are L Lawliet from CKCET. SPARK Cortex is a small chip that learns new things after it has shipped, without forgetting the old ones, and without a multiplier or backpropagation. One promise before we start: every number I show is labelled as simulated, estimated or measured, and nothing is measured on hardware yet.

## Slide 2: AI stops learning the day it ships

A normal neural network learns once. Teach it five new things in five stages and it keeps only the last stage: 19.5 percent on digits, 20 on clothing, 16 on spoken words (simulated, 5 seeds). The usual fix is to retrain from scratch, which costs energy and, in the end, hardware that is discarded. We asked what a chip would look like if it could keep learning like a brain.

## Slide 3: The idea: a human brain, as a chip

Our rule is to follow the brain, not the GPU. Four things: senses that learn without labels; learning by counting, one example at a time; sleep, where the chip dreams old classes from small counters instead of storing examples; and sharing, because counts can simply be added together. There is no multiplier anywhere in the design.

## Slide 4: It learns in stages and keeps what it knew

Here is the core result. Learning five stages of two classes each, the chip with the slow-table option keeps 95.9 percent on digits, 81.4 on clothing and 83.6 on spoken words (95.8, 78.3 and 82.9 without it), while a network that fine-tunes on each stage drops to roughly a fifth. This is simulated with the exact integer model, five seeds, and the RTL is bit-exact with it. Even one class at a time, with today's design, it holds 94 percent on digits and 79 on clothing.

## Slide 5: A new class from one example, after shipping

We found a failure and redesigned for it: a brand-new class seen only once was almost invisible. The fix is called IMPRINT: when an example looks new, the chip writes its mean code into the table row immediately, then a short sleep of 300 dreams per known class blends it in. Digits go from 54 to 70, clothing 50 to 64, words only 45 to 48. It is implemented in the RTL and checked bit-exact.

## Slide 6: It hears: raw sound to word

The sound path goes from raw samples through a cochlea, a noise-floor stage, the encoder and the learning core, all in RTL and bit-exact with the model. A word-alignment step that shifts each word so its start lands at the same frame lifted accuracy from 71.9 to 82.5 percent all at once, and the chip stays usable in noise: 72 percent at 20 dB, 59 at 10 dB. Sound needs 422 kilobytes of memory, which does not fit the small board.

## Slide 7: Knowledge moves between chips

Because the memory is counts, two chips that learned different classes can be merged by adding their counters, or one chip can hand its memory to another that keeps learning. Merge gives 93, 81 and 64 percent; hand-over gives 96, 83 and 72. This is the weight-transfer story: no retraining on a server. The board demo reached 91.4 percent on all ten digits in the bit-exact emulator.

## Slide 8: We found what limited the scores

We asked what actually limits the scores and tested it. A floating-point classifier trained on the chip's own code reaches 87.9 percent on clothing and 98.3 on digits, so the senses are not the limit. The chip's one-pass 5-bit readout is. A slow second table that follows the fast one, slowly, fixes most of that: clothing 83.4 to 87.6, words 83 to 86, digits 97.0 to 97.8, and staged clothing 78.4 to 81.6, because slow consolidation damps the bias toward the newest classes. It uses shifts and adds only and is checked bit-exact in the RTL. A finer detector grid for images adds a little more all at once, but it made staged digits worse in an earlier setting, so it stays an option. All simulated.

## Slide 9: Small, cheap, and no multiplier

Cost. The image memory is 84 kilobytes. It fits a 25-dollar Tang Nano 20K with no hardware multipliers and timing met. Counting only the operations a decision needs, it uses about 74 times less energy than an 8-bit network, an estimate. I want to be careful: the layout estimate is higher, about a fifth of a microjoule per decision, so the honest wording is 74 times less per operation needed, not per chip.

## Slide 10: Verified bit for bit, and laid out

The design is not just a simulator result. Twenty-one bit-exact checks pass between the integer model and the RTL, covering the core, the few-shot fix, the sense layers, the whole sound chain and the board top. We also took it through an open-source SKY130 layout flow; detailed routing ended at one remaining violation at a memory macro edge. That is an estimate, with no sign-off and no fabrication.

## Slide 11: Where it is level, and where it is weaker

This is the slide I want you to remember. Learning everything at once, with the slow-table option, the chip is level with a small network: 98.4 against 97.8 on digits, 88.3 against 87.3 on clothing, 87.5 against 85.5 on words, simulated, five seeds. Level, not better: a small convolutional network reaches about 89 on clothing and 91 on words. In stages clothing is 81 percent, digits 95 and words 83. New spoken words from one to five recordings are weak. We tried many fixes and recorded the failures, such as a second sensory layer, wider sound detectors and a shared prototype pool. And nothing is measured on hardware yet.

## Slide 12: Not the first, and what is new

We are not the first continual-learning chip. Hyperdimensional-computing accelerators and Intel's Loihi 2 exist. What is new is the combination: dreams generated from small counters so no examples are stored, a night that ends by itself, no multipliers, and a design that is bit-exact from raw senses to the decision. Against hyperdimensional computing in our own test, after five stages we are ahead on digits by 2.2 and on sound by 5.7 points, simulated.

## Slide 13: What comes next

What comes next. The model, RTL and layout estimate are done. The next milestone is the real board, which gives the first measured numbers. Then we work on the weak spots, learned word features and higher-fidelity dreams for clothing. The horizon is a provable result within six to eight months, with no fabrication yet.

## Slide 14: Close

To close: SPARK Cortex is a chip that keeps learning after it ships. It keeps what it knew, shares what it learned, and needs no multiplier. It is weaker than a network in a few places, and I have told you where. Thank you, I am happy to take questions.

Related: [Q&A sheet](pitch_qa_sheet.md), [Claims sheet](cortex_claims_sheet.md), [Results at a glance](results_at_a_glance.md), [Old script](pitch_script.md), [Project memory](PROJECT_MEMORY.md)
