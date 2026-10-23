---
title: Status report 24 Oct 2026
tags: [l, status, report]
---

# Status report (plain words), 24 Oct 2026

**Bottom line.** The L chip design is sound and bit-exact in simulation; its memory at inference is small; it learns in stages with about a tenth of the memory of a replay baseline. It does **not** beat a CNN on accuracy (clothing 88.9 against 91.1, Shirt 64 to 74 against 79) and none of the cheap fixes tried closes that. The tile layout is not finished (routing failed). Nothing has been built or measured on silicon or on the boards.

## What is done and trustworthy (label in brackets)
- Tile RTL (router, bank, sequencer), mesh and sequencer bit-exact; board top for one tile passes a UART simulation; Gowin synthesis 1,014 cells + 32 block RAMs for 64 KB (SIMULATED / synthesis). [tile_board_prep](../hw/results/tile_board_prep.md)
- ESP32 test kit ready (logic verified on a PC build, 0 of 200 differ); no board result yet. [ESP32 README](../hw/board/esp32_l_test/README.md)
- Deployed L table: 11 KB (2 bits per entry) still 88.65% on clothing; about 10 times smaller than the 4-bit MLP for 0.9 points less (SIMULATED). [l_deployed_memory](../hw/results/l_deployed_memory.md)
- Staged learning against fair baselines: EWC about 20%; replay needs about 1.5 MB for L's 81.5% (clothing) and 94.2% (digits); L needs about 130 KB learning state (MEASURED, 3 seeds). [staged_replay_baselines](../hw/results/staged_replay_baselines.md)
- Research report on matrix-free models (second-hand numbers; paper sites were blocked). [report](research/matrix_free_vs_cnn_report.md)
- GPU limits against L (ESTIMATED, recalled public figures). [gpu_limits_and_L](gpu_limits_and_L.md)

## Failures and weak spots (recorded as clearly as wins)
- **Tile routing failed twice** (stalled near 300 violations, then killed for memory). Needs a looser floorplan or a different router setting. Tile LVS, antenna fix, final DRC and measured-activity power for the tile are therefore not done.
- **Neural baseline beats the counting language model at equal memory below about 0.5 MB** ([neural_vs_counting_lm](../hw/results/neural_vs_counting_lm.md)).
- **Compressed MLP forgets (about 20%) like the CNN, but with replay it matches L** (above).
- **Clothing**: Shirt recall 64 to 74% in every variant; extra passes, specialists, hand-made shape cues, HOG bits and conjunction features gave at most +0.9 points; a gradient-trained lookup layer gave no gain. A spoken-name "second sense" test was withdrawn (the name is the label). Colour helps the Shirt/T-shirt pair on real photos (61 to 80% Shirt recall, small noisy data); the colour-opponent and held-out-volunteer test was not finished. [clothing_features_round](../hw/results/clothing_features_round.md), [shirt_real_photos](../hw/results/shirt_real_photos.md)

## What the user must do
1. Order the INA219 sensor (about Rs 100 to 300) and, with it, the Tang Nano 20K (about Rs 4,200); run the ESP32 logic and speed line now (needs no extra part) and send the `RUN` line.
2. Find a university or programme partner for a foundry memory compiler and shuttle access.
3. Decide the pitch line: claim memory at equal accuracy and staged learning against replay, not "beats a CNN".

## Next (proposed)
1. Route the tile with a looser floorplan; then LVS, antenna fix, DRC.
2. Decide whether to start the accelerator path: a gradient-trained multi-layer lookup or clause network (matrix-free inference), which is where CNN-level Fashion-MNIST accuracy could come from.
3. Finish the colour-opponent and held-out-volunteer test on real photos.

Related: [Docs index](INDEX.md), [Journal](journal.md), [Project memory](PROJECT_MEMORY.md), [Results index](../hw/results/INDEX.md)
