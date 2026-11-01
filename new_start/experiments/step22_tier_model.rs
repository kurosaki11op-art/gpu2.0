// Step 22: SRAM plus DRAM tier on each chip, against an H100-class GPU cluster, 1T mixture-of-experts at batch 1 (1 Nov 2026). MODELLED, every parameter ASSUMED unless marked.
// Plan and pre-set bars: new_start/step22_tier_plan.md. G3-count: our chips <= 2x GPUs. G3-speed: our speed per user >= 4x the GPU cluster's. Both needed.
// Build: rustc -O step22_tier_model.rs -o step22 ; run: ./step22
const W_TOTAL: f64 = 1000e9; const W_ACTIVE: f64 = 32e9; const BITS: f64 = 4.0; const LAYERS: f64 = 61.0; const D: f64 = 7168.0; const KVDIV: f64 = 16.0; const CTX: f64 = 4096.0; const KV_B: f64 = 2.0;
const GPU_CAP: f64 = 72e9; const GPU_BW: f64 = 3.35e12; const GPU_EFF: f64 = 0.8; // 80% of the memory floor: test B measured 72% to 95% on a T4 with graphs
const SRAM_GB: f64 = 0.8 * 800.0 / 420.0; const TILE_B: f64 = 4194304.0; const TILE_BW: f64 = 256e9; // M3 tile rate, 1 GHz
const OVERHEAD_S: f64 = 50e-6; // per-token network and software overhead (striping runs: 33 to 70 microseconds)
const E_SRAM: f64 = 0.55; const E_DRAM: f64 = 5.74; // pJ per bit; SRAM from the step 6 model, DRAM tier at the HBM figure
const CHIP_USD: f64 = 480.0 + 125.0; const TIER_USD_GB: f64 = 15.0; // chip central cost plus host adder (step 21); tier price per GB from the step 3 notes (HBM $12 to 17 per GB), unsourced for our volume
const GPU_USD_MFG: f64 = 3320.0 * 1.5; const GPU_USD_SELL: f64 = 25000.0 * 1.5; // step 21 manufacturing cost and selling price, host overhead 1.5
const LIFE_S: f64 = 4.0 * 365.0 * 86400.0; const UTIL: f64 = 0.5; const KWH: f64 = 0.10; const PUE: f64 = 1.3;
fn main() {
    let kvseq = 2.0 * LAYERS * (D / KVDIV) * CTX * KV_B; let wtot = W_TOTAL * BITS / 8.0; let t_bytes = W_ACTIVE * BITS / 8.0 + kvseq; // bytes read per token at batch 1 (active weights plus the whole cache)
    let ng = ((wtot + kvseq) / GPU_CAP).ceil(); let tg = t_bytes / (GPU_EFF * ng * GPU_BW); let sg = 1.0 / tg;
    let eg = t_bytes * 8.0 * E_DRAM * 1e-12; let cost_g = |usd: f64| ng * usd / LIFE_S / (sg * UTIL) * 1e6 + eg * PUE * KWH / 3.6e6 * 1e6;
    println!("MODELLED, not measured. 1T MoE (32B active), 4-bit, context {}, batch 1. Bytes read per token {:.1} GB (weights {:.1}, cache {:.2}); weights plus cache {:.1} GB.", CTX, t_bytes / 1e9, W_ACTIVE * BITS / 8.0 / 1e9, kvseq / 1e9, (wtot + kvseq) / 1e9);
    println!("GPU cluster: {} GPUs, {:.0} tokens/s per user at {:.0}% of the memory floor, {:.3} J/token, cost per million tokens ${:.3} (manufacturing-cost basis) to ${:.3} (selling-price basis).", ng, sg, GPU_EFF * 100.0, eg, cost_g(GPU_USD_MFG), cost_g(GPU_USD_SELL));
    let sbw = SRAM_GB * 1e9 / TILE_B * TILE_BW; println!("Our chip: SRAM {:.2} GB, SRAM read bandwidth {:.0} TB/s, overhead {:.0} microseconds per token.\n", SRAM_GB, sbw / 1e12, OVERHEAD_S * 1e6);
    println!("{:>7} {:>7} {:>6} | {:>6} {:>7} | {:>6} {:>9} {:>7} | {:>10} {:>8} | {:>8}", "tier GB", "tier TB/s", "hit h", "chips", "x GPUs", "tok/s", "speed x", "J/tok", "$/Mtok", "energy x", "count ok");
    let mut need: Vec<(f64, f64, f64, f64, f64)> = Vec::new();
    for &c in &[0.0f64, 24.0, 48.0, 96.0] { for &bw in &[0.8f64, 1.6] {
        let n = ((wtot + kvseq) / (SRAM_GB * 1e9 + c * 1e9)).ceil(); let cnt = n / ng; let usd = n * (CHIP_USD + c * TIER_USD_GB);
        let mut hstar: Option<f64> = None;
        for &h in &[0.0f64, 0.25, 0.5, 0.75, 0.9, 1.0] {
            if c == 0.0 && h < 1.0 { continue; } // no tier: everything is in SRAM
            let t = (h * t_bytes / (n * sbw)).max(if h < 1.0 { (1.0 - h) * t_bytes / (n * bw * 1e12) } else { 0.0 }) + OVERHEAD_S; let s = 1.0 / t; let e = t_bytes * 8.0 * (h * E_SRAM + (1.0 - h) * E_DRAM) * 1e-12;
            let cost = usd / LIFE_S / (s * UTIL) * 1e6 + e * PUE * KWH / 3.6e6 * 1e6;
            println!("{:>7.0} {:>7.1} {:>6.2} | {:>6.0} {:>6.1}x | {:>6.0} {:>8.2}x {:>7.3} | {:>10.3} {:>7.1}x | {:>8}", c, bw, h, n, cnt, s, s / sg, e, cost, eg / e, if cnt <= 2.0 { "yes" } else { "no" });
        }
        // smallest h (fine scan) meeting speed 4x
        for k in 0..=1000 { let h = k as f64 / 1000.0; let t = (h * t_bytes / (n * sbw)).max(if h < 1.0 { (1.0 - h) * t_bytes / (n * bw * 1e12) } else { 0.0 }) + OVERHEAD_S; if 1.0 / t >= 4.0 * sg { hstar = Some(h); break; } }
        need.push((c, bw, cnt, hstar.unwrap_or(f64::NAN), n));
    } }
    println!("\nBAR SUMMARY (G3-count: chips at most 2x the GPUs; G3-speed: at least 4x the GPU speed per user):");
    for (c, bw, cnt, h, n) in need { println!("  tier {:>3.0} GB at {:.1} TB/s: {:.0} chips ({:.1}x GPUs) -> count bar {}; speed bar needs SRAM hit rate h >= {} -> {}", c, bw, n, cnt, if cnt <= 2.0 { "PASS" } else { "FAIL" }, if h.is_nan() { "(not reachable)".to_string() } else { format!("{:.3}", h) }, if cnt <= 2.0 && !h.is_nan() { "both bars can hold together only at that h (h is UNKNOWN)" } else { "cannot pass both" }); }
}
