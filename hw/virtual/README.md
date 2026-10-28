---
title: Virtual FPGA device VFPGA-L1 and its tests
tags: [spark, virtual, fpga, tests, hardware]
---

# Virtual FPGA device (hw/virtual)

A simulation target for the three-layer L design, built before any real FPGA is bought (founder's request, 28 Oct 2026): a resource-limited virtual device, a regression that runs the whole design on it in simulation, hostile-input stress tests, and a rotatable 3D view of the floorplan with replayed jobs. **Everything is simulation (iverilog) and synthesis estimates (yosys, Gowin family); no board, no place and route, no timing closure, no power.**

- `vfpga_device.json`: the device (50 MHz virtual clock, 20,000 logic cells, 120 block RAMs of 18 Kbit, 48 multipliers of 9 x 9, UART), sized with headroom for the design. A simulation target, not a real part.
- `vfpga.py`: synthesises each block and the whole board top and checks the counts against the device budget (`results/synth_resources.json`).
- `run_all.py`: the full regression (`--quick` skips the 10,000-image run and the synthesis); writes `results/test_summary.json`.
- Test 1 `run_full_testset.py`: all 10,000 test images through the system RTL, compared image by image with the independent reference model `hw/brain/experiments/month5/ldeep_ref.py` (written from the RTL memory files only).
- Test 2 `run_stress_top.py`: a stress mix on the layered top (random and corner inputs, matrix products interleaved, reset injected mid-job, repeated images).
- Test 3 `run_stress_forge.py`: 200,000 random lane operations and the matrix-product tile on seven data distributions.
- Test 4 `run_stress_board.py`: the UART board top under junk bytes, invalid ops and stray sync bytes.
- `vfpga_3d.html` (standalone) and `vfpga_3d_artifact.html`: the 3D board, built by `build_3d.py` from the results; open the file in a browser (fonts load from the web, the 3D is plain canvas code).

Results and findings: [Virtual device tests](../results/virtual_device_tests.md).

Related: [Hardware index](../HARDWARE_INDEX.md), [L chip top](../rtl/top/README.md), [Status, 28 Oct 2026](../../docs/L_status_28oct.md)
