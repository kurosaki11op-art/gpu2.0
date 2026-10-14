"""ESTIMATED energy per decision and per learning step: SPARK Cortex vs a small neural network (784-256-10).

Operation counts come from the design (active code bits measured on the test images; memory word sizes from the RTL).
Energy per operation: Horowitz, "Computing's energy problem", ISSCC 2014, 45 nm, 0.9 V:
  8-bit add 0.03 pJ, 32-bit add 0.1 pJ, 8-bit multiply 0.2 pJ, 32-bit float add 0.9 pJ, 32-bit float multiply 3.7 pJ,
  SRAM 64-bit read: 8 KB 10 pJ, 32 KB 20 pJ, 1 MB 100 pJ. Writes are taken equal to reads. A 25-bit match count
  (XNOR + popcount) is taken as 25 1-bit adds ~ 25 x 0.03/8 pJ, rounded up to 0.2 pJ.
These are order-of-magnitude estimates for a custom chip, not FPGA numbers and not measurements.
usage: python energy_cortex.py DATA_DIR"""
import json, os, sys
import numpy as np

D = sys.argv[1]
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); act = float(z["te"].sum(1).mean())
E = {"add8": 0.03, "add32": 0.1, "mul8": 0.2, "fadd": 0.9, "fmul": 3.7, "sram8k": 10, "sram32k": 20, "sram1m": 100,
     "match25": 0.2}
NB, C, POS, CH, FD = 4608, 10, 144, 4, 32                                  # code bits, classes, patch spots, channels, detectors
# ---- SPARK Cortex ---------------------------------------------------------------------------------------------------
enc = POS * CH * FD * E["match25"] + POS * CH * FD * E["add8"]               # match every detector at every spot + max
dec = act * E["sram32k"] + act * C * E["add32"]                              # one 50-bit table word per active bit, 10 adds
learn = dec + act * E["sram32k"] * 2 + act * E["add8"]                       # + count read-modify-write (dream counts)
upd = act * E["sram32k"] * 2 + act * 2 * E["add8"]                          # surprise update (table read-modify-write)
dream = NB * (E["sram32k"] / 2 + 1.3 * 3 * E["add32"]) + dec                 # read a count per bit, ~1.3 random draws, practise
# ---- neural network 784-256-10 ----------------------------------------------------------------------------------------
macs = 784 * 256 + 256 * 10; wbytes = macs
nn_int8 = macs * (E["mul8"] + E["add32"]) + wbytes / 8 * E["sram1m"] / 4    # int8 weights in a ~200 KB SRAM (~25 pJ/read)
nn_fp32 = macs * (E["fmul"] + E["fadd"]) + wbytes * 4 / 8 * E["sram1m"]
nn_train_fp32 = 3 * nn_fp32                                                   # forward + backward + weight update
R = {"label": "ESTIMATED (45 nm per-operation energies, operation counts from the design)",
     "active_code_bits_per_image": act,
     "cortex_nJ": {"sense_encode": enc / 1e3, "decide": dec / 1e3, "decide_incl_encode": (enc + dec) / 1e3,
                   "learn_one_example_incl_encode_and_update": (enc + learn + upd) / 1e3, "one_dream_practised": dream / 1e3},
     "network_nJ": {"decide_int8": nn_int8 / 1e3, "decide_fp32": nn_fp32 / 1e3, "train_step_fp32_per_example": nn_train_fp32 / 1e3},
     "ratios": {"decide_int8_vs_cortex": nn_int8 / (enc + dec), "train_fp32_vs_cortex_learn": nn_train_fp32 / (enc + learn + upd)}}
print(json.dumps(R, indent=1))
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "cortex_energy_estimate.json"), "w"), indent=1)
