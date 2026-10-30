// 30 Oct 2026, MODEL (analytic energy and capacity model; every constant is an assumption or a cited reference, nothing here is measured except the 6 W idle power of the founder's laptop RTX 3050).
// New start, target 3 (language-model inference), charter-style step 1, written BEFORE the first run:
// QUESTION: at batch 1 a GPU generating tokens is memory-bound (every token re-reads all the weights from DRAM). How much energy per token would a machine that keeps the weights in on-chip SRAM save, and at what silicon capacity?
// PASS BAR (set in advance): for a model of at least 1 billion parameters at 4-bit weights, batch 1, context 2,048: energy per token at least 5x lower than the GPU-style machine, using the PESSIMISTIC SRAM energy of the range, AND the on-chip capacity needed (weights + key/value cache) at most 1 GB (the one-die budget of the project's SRAM cost model, about 341 mm2).
// IF IT FAILS: target 3 is dropped as a first target.
// Build: rustc -O step1_lm_decode_model.rs   Standard library only.
//
// Per generation step of a batch of B sequences (each producing one token):
//   weights W = N * bits / 8 bytes, read once per step (shared by the batch); key/value cache read per sequence: 2 * layers * d * L * 2 bytes (16-bit, no grouped-query saving); multiply-adds per token: N + 2 * layers * d * L.
//   GPU-style: all bytes come from DRAM at E_DRAM pJ/bit (project value for HBM3E, 5.74; GDDR6 is higher, so this favours the GPU), time = max(bytes / bandwidth, MACs / peak), plus board static power x time.
//   Chip: weights and cache in SRAM at E_SRAM pJ/bit (project range 0.495 to 2.78), compute-bound time, plus static power (logic 0.5 W + leakage 0.5 W per GB; project range 0.2 to 1.6 W per GB).
//   MAC energy by weight width (assumed, same for both machines): 16-bit 1.5 pJ, 8-bit 0.25 pJ, 4-bit 0.12 pJ, ternary 0.06 pJ.
const E_DRAM: f64 = 5.74; const E_SRAM_LO: f64 = 0.495; const E_SRAM_MID: f64 = 1.0; const E_SRAM_HI: f64 = 2.78;
const BW_GPU: f64 = 168e9; // bytes/s, an RTX 3050 6 GB class card (assumed)
const PEAK: f64 = 10e12;   // multiply-adds per second, the same for both machines (assumed)
const P_STATIC_GPU: f64 = 6.0; // W, MEASURED idle power of the founder's laptop RTX 3050 (a floor: a loaded board draws more)
const MM2_PER_GB: f64 = 341.0; const COST_PER_GB: f64 = 200.0; // project SRAM cost model: 1 GB = 341 mm2 and about $223; 4 GB about $174 per GB
fn mac_pj(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else if bits >= 8.0 { 0.25 } else if bits >= 4.0 { 0.12 } else { 0.06 } }
struct M { name: &'static str, n: f64, layers: f64, d: f64 }
fn gpu(m: &M, bits: f64, b: f64, l: f64) -> (f64, f64) { // (joules per token, tokens per second per sequence)
    let w = m.n * bits / 8.0; let kv = 2.0 * m.layers * m.d * l * 2.0; let bytes = w + b * kv; let macs = b * (m.n + 2.0 * m.layers * m.d * l);
    let t = (bytes / BW_GPU).max(macs / PEAK); let e = bytes * 8.0 * E_DRAM * 1e-12 + macs * mac_pj(bits) * 1e-12 + P_STATIC_GPU * t; (e / b, 1.0 / t)
}
fn chip(m: &M, bits: f64, b: f64, l: f64, e_sram: f64) -> (f64, f64, f64) { // (joules per token, tokens/s per sequence, capacity GB)
    let w = m.n * bits / 8.0; let kv = 2.0 * m.layers * m.d * l * 2.0; let bytes = w + b * kv; let macs = b * (m.n + 2.0 * m.layers * m.d * l); let cap = (w + b * kv) / 1e9;
    let t = macs / PEAK; let p_static = 0.5 + 0.5 * cap; let e = bytes * 8.0 * e_sram * 1e-12 + macs * mac_pj(bits) * 1e-12 + p_static * t; (e / b, 1.0 / t, cap)
}
fn main() {
    let models = [M { name: "125M", n: 125e6, layers: 12.0, d: 768.0 }, M { name: "1B", n: 1.0e9, layers: 16.0, d: 2048.0 }, M { name: "7B", n: 7.0e9, layers: 32.0, d: 4096.0 }, M { name: "70B", n: 70.0e9, layers: 80.0, d: 8192.0 }];
    let l = 2048.0;
    println!("MODEL, not a measurement. Context {} tokens. GPU-style: DRAM {} pJ/bit, {} GB/s, board static {} W (MEASURED idle of an RTX 3050 laptop). Chip: SRAM {} to {} pJ/bit, compute-bound.", l, E_DRAM, BW_GPU / 1e9, P_STATIC_GPU, E_SRAM_LO, E_SRAM_HI);
    println!("energy per token in millijoules; ratio = GPU / chip; chip cases use the PESSIMISTIC SRAM energy (2.78 pJ/bit), middle value (1.0) in brackets; capacity = weights + KV cache for ONE sequence.\n");
    println!("{:<6} {:<5} {:<5} | {:>9} {:>9} | {:>9} {:>9} {:>8} | {:>8} {:>8} {:>8} | {:>8} {:>9} {:>8}", "model", "bits", "batch", "GPU mJ", "GPU tok/s", "chip mJ", "[mid]", "ratio", "ratio B8", "ratio B64", "ratio mid", "cap GB", "area mm2", "cost $");
    let mut pass_all = true; let mut any = false;
    for m in &models {
        for &bits in &[16.0, 8.0, 4.0, 1.58] {
            let b = 1.0; let (eg, tg) = gpu(m, bits, b, l); let (ec, _tc, cap) = chip(m, bits, b, l, E_SRAM_HI); let (ecm, _, _) = chip(m, bits, b, l, E_SRAM_MID);
            let r8 = gpu(m, bits, 8.0, l).0 / chip(m, bits, 8.0, l, E_SRAM_HI).0; let r64 = gpu(m, bits, 64.0, l).0 / chip(m, bits, 64.0, l, E_SRAM_HI).0;
            println!("{:<6} {:<5} {:<5} | {:>9.3} {:>9.1} | {:>9.3} {:>9.3} {:>7.1}x | {:>7.1}x {:>8.1}x {:>7.1}x | {:>8.2} {:>9.0} {:>8.0}", m.name, bits, 1, eg * 1e3, tg, ec * 1e3, ecm * 1e3, eg / ec, r8, r64, eg / ecm, cap, cap * MM2_PER_GB, cap * COST_PER_GB);
            if m.name == "1B" && bits == 4.0 { any = true; let ok = eg / ec >= 5.0 && cap <= 1.0; println!("       -> BAR (the smallest model of >= 1B parameters, 4-bit): ratio {:.1}x (>= 5x needed), capacity {:.2} GB (<= 1 GB needed): {}", eg / ec, cap, if ok { "PASS" } else { "FAIL" }); pass_all = ok; }
        }
    }
    println!("\nVERDICT by the pre-set bar (applied to the 1B model at 4-bit, the smallest that counts): {}", if any && pass_all { "PASS" } else { "FAIL" });
    println!("The 7B and 70B rows need several dies (capacity above 1 GB), whose links are not modelled; their ratios are shown for direction only.");
}
