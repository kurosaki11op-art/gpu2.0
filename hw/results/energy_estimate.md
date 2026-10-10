# SPARK energy per token — MODELLED from MEASURED operation counts

Operation counts come from the bit-exact golden model (the RTL matches it with 0 mismatches): which stages run
per token, how many input events each stage processes (weight words read, multiply-accumulates) and the
neuron pass over every output of each stage that runs, plus recall-table accesses.
Energy per operation: Horowitz, "Computing's energy problem (and what we can do about it)", ISSCC 2014, 45 nm —
5 pJ per 32-bit on-chip SRAM weight word, 0.1 pJ per int4 MAC, 7.5 pJ per neuron pass (3 × 16-bit SRAM accesses,
conservative), 20 pJ per token for recall. Script: `hw/energy/energy_model.py`. 2,000 held-out bytes.

**This is an estimate (label: MODELLED). Board watts are not measured yet.**

## Sparsity-0.05 model
| Setting | Accuracy | Weight words/token | Energy/token | vs compute-all | Range (±2× MAC/neuron energy) | If weights came from DRAM |
|---|---|---|---|---|---|---|
| Compute every neuron (GPU-style dense) | 59.9% | 9,216 | 57.3 nJ | 1× | — | 1× |
| Skip silent neurons | 59.9% | 4,174 | 28.1 nJ | 2.0× less | 1.9–2.1× | 2.2× |
| Effort LOW (memory answers) | 68.1% | 1,089 | 7.3 nJ | **7.9× less** | 7.5–8.1× | 8.5× |
| Effort MEDIUM (fresh state) | 70.5% | 2,501 | 16.8 nJ | 3.4× less | 3.3–3.5× | 3.7× |
| Effort HIGH (arbitration) | 72.6% | 3,280 | 22.6 nJ | **2.5× less** | 2.4–2.6× | 2.8× |

## Sparsity-0 model
| Setting | Accuracy | Energy/token | vs compute-all |
|---|---|---|---|
| Compute every neuron | 63.9% | 57.3 nJ | 1× |
| Skip silent neurons | 63.9% | 38.9 nJ | 1.5× less |
| Effort LOW | 69.2% | 11.9 nJ | 4.8× less |
| Effort MEDIUM | 71.6% | 23.5 nJ | 2.4× less |
| Effort HIGH | 73.8% | 32.1 nJ | 1.8× less |

## Water (PROJECTED)
Data-centre cooling water scales with the energy that becomes heat, so a 2.5–7.9× energy cut per token is a
60–87% cut in cooling water per token at the same water-use efficiency. This is a proportional projection,
not a measurement, and assumes SPARK-style processing at data-centre scale.

## Limits
- Baseline is our own core in dense mode, not a GPU.
- Static/leakage power and clocking are not included; on an FPGA, static power is large, so measured board
  savings will be smaller than these dynamic-energy ratios. Energy per token still falls with fewer cycles.
