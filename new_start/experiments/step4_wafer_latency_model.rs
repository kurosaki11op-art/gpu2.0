// 31 Oct 2026, MODEL (analytic; nothing here is measured). Closing rows I and J of docs/gpu_workload_map.md. Written BEFORE the first run.
// Step 3 left three hinges, all ASSUMED: (1) the step latency of a wafer machine (0.5 ms), (2) the system hardware cost ($150k), (3) the GPU's decode power and price.
// This step replaces (1) by a layer-by-layer latency model of a pipelined wafer (each layer's weights stay in their own region; tokens of different sequences flow through the layers),
// and turns (2) and (3) into THRESHOLDS: the highest hardware cost and the lowest GPU power at which the bars still pass, so the open items become supplier quotes and one measurement.
//
// PRE-SET BARS (applied as written; no constant changed after the run):
//   L1: modelled latency of one token through the 1T mixture-of-experts model (4-bit, 64 sequences, context 4,096) on L-wafer A is at most 2 ms (the level at which step 3 showed I2 and J2 still holding).
//   I2': at the bottom-up price with the modelled latency, cost per million tokens is at most 0.5x the GPU cluster, and the HIGHEST system hardware cost that still passes is printed (bar: that threshold is at least $150k).
//   J2': facility energy per token at least 5x below the GPU cluster at the pessimistic SRAM energy for every GPU decode power from 220 W to 700 W (at 100 W the result is printed, as the floor).
//   J1': heat density at most 1.0 W/mm2 (as step 3).
//   X : the cited wafer (same model, 23 kW drawn throughout) is shown for reference; no bar.
// Build: rustc -O step4_wafer_latency_model.rs   Standard library only.
//
// LATENCY MODEL (all ASSUMED unless marked): a layer's region is wafer_area / layers_per_wafer; one fabric phase (a broadcast or a reduction across the region) takes
//   (region side / tile side) hops x 1 ns per hop; a layer has 6 dependent phases (QKV broadcast, score reduction, value reduction, output projection, expert up broadcast, expert down reduction);
//   compute per layer-token = (active params / layers + 2 d L) multiply-adds at the region's share of peak; read = the active weight bytes of the layer plus its KV bytes at the region's share of SRAM bandwidth;
//   each wafer-to-wafer crossing adds 1 us (link). Tile 0.05 mm2 (derived from the cited 46,225 mm2 / 900,000 cores). Throughput = min(B, layers) / token latency (a full pipeline).
// COST and POWER inputs are those of step 3 (see step3_cost_power_result.md for sources and labels).
const WAFER_300: f64 = 70686.0; const WAFER_PRICE: f64 = 18500.0; const WAFER_MM2: f64 = 46225.0; const MM2_PER_GB: f64 = 341.0; const TILE_MM2: f64 = 0.05; const SPARE: f64 = 0.01;
const E_HBM: f64 = 5.74; const E_HI: f64 = 2.78; const L: f64 = 4096.0; const E_LINK: f64 = 10.0; const HOP_S: f64 = 1e-9; const PHASES: f64 = 6.0; const LINK_S: f64 = 1e-6;
const GPU_BW: f64 = 3.35e12; const GPU_PEAK: f64 = 495e12; const GPU_CAP: f64 = 72e9; const GPU_OVERHEAD: f64 = 1.5; const GPU_MM2: f64 = 814.0;
const CB_CAP: f64 = 44e9; const CB_BW: f64 = 21e15; const CB_PEAK: f64 = 62e15; const CB_P: f64 = 23000.0; const CB_PRICE: f64 = 2.5e6;
const LW_PEAK: f64 = 10e15; const BW_PER_BYTE: f64 = 21e15 / 44e9; const SYS_HW: f64 = 150000.0;
const KWH: f64 = 0.10; const LIFE_S: f64 = 4.0 * 365.0 * 86400.0; const UTIL: f64 = 0.5; const PUE_AIR: f64 = 1.4; const PUE_LIQ: f64 = 1.15;
// latency calibration factor: the model was 1.7x to 1.8x faster than the vendor-reported per-user speeds (see the calibration block); default 1.8 applies that correction (env LAT_SCALE=1 gives the uncalibrated run, log step4_run1_uncalibrated.log)
fn lat_scale() -> f64 { std::env::var("LAT_SCALE").ok().and_then(|v| v.parse().ok()).unwrap_or(1.8) }
fn mac_pj(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else if bits >= 8.0 { 0.25 } else { 0.12 } }
struct M { name: &'static str, total: f64, active: f64, layers: f64, d: f64, kv_div: f64 }
struct S { wtot: f64, bytes: f64, kvseq: f64, macs: f64 }
fn step(m: &M, bits: f64, b: f64) -> S {
    let wtot = m.total * bits / 8.0; let f = m.active / m.total; let touched = if f >= 0.999 { 1.0 } else { 1.0 - (1.0 - f).powf(b) };
    let kvseq = 2.0 * m.layers * (m.d / m.kv_div) * L * 2.0; let macs = b * (m.active + 2.0 * m.layers * m.d * L);
    S { wtot, bytes: wtot * touched + b * kvseq, kvseq, macs }
}
struct R { n: f64, t: f64, p_w: f64, ej: f64, capex: f64, density: f64, pue: f64, lat: f64 } // lat: seconds for one token through all layers (0 for GPUs: not needed)
fn units_for(s: &S, b: f64, cap: f64) -> f64 { ((s.wtot + b * s.kvseq) / cap).ceil().max(1.0) }
// token latency through the layers on n wafers; returns (latency, time per step of b tokens)
fn latency(m: &M, bits: f64, b: f64, n: f64, peak: f64, bw: f64) -> (f64, f64) {
    let lpw = (m.layers / n).ceil(); let region = WAFER_MM2 / lpw; let hops = region.sqrt() / TILE_MM2.sqrt();
    let fabric = PHASES * hops * HOP_S; let macs_l = m.active / m.layers + 2.0 * m.d * L; let comp = macs_l / (peak / lpw);
    let bytes_l = m.active * bits / 8.0 / m.layers + 2.0 * m.d / m.kv_div * L * 2.0; let read = bytes_l / (bw / lpw);
    let stage = fabric + comp + read; let lat = (m.layers * stage + (n - 1.0) * LINK_S) * lat_scale(); let thr = b.min(m.layers) / lat; (lat, b / thr)
}
fn gpu(m: &M, bits: f64, b: f64, w: f64, price: f64) -> R {
    let s = step(m, bits, b); let n = units_for(&s, b, GPU_CAP); let t = (s.bytes / (GPU_BW * n)).max(s.macs / (GPU_PEAK * n));
    let e = s.bytes * 8.0 * E_HBM * 1e-12 + s.macs * 0.25e-12 + w * n * t;
    R { n, t, p_w: e / t, ej: e / b, capex: n * price * GPU_OVERHEAD, density: e / t / n / GPU_MM2, pue: PUE_AIR, lat: t }
}
fn cb(m: &M, bits: f64, b: f64) -> R {
    let s = step(m, bits, b); let n = units_for(&s, b, CB_CAP); let (lat, t) = latency(m, bits, b, n, CB_PEAK * n / n, CB_BW);
    let dyn_j = s.bytes * 8.0 * E_HI * 1e-12 + s.macs * mac_pj(bits) * 1e-12; let e = dyn_j.max(CB_P * n * t);
    R { n, t, p_w: e / t, ej: e / b, capex: n * CB_PRICE, density: e / t / n / WAFER_MM2, pue: PUE_LIQ, lat }
}
fn lw(m: &M, bits: f64, b: f64, e_sram: f64, leak: f64, unit_price: f64) -> R {
    let gb = 0.8 * WAFER_MM2 / MM2_PER_GB; let cap = gb * 1e9; let s = step(m, bits, b); let n = units_for(&s, b, cap);
    let (lat, t) = latency(m, bits, b, n, LW_PEAK, BW_PER_BYTE * cap); let link = (n - 1.0) * m.d * 2.0 * 8.0 * E_LINK * 1e-12 * b;
    let e = s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + (0.5 + leak * gb) * n * t + link;
    R { n, t, p_w: e / t, ej: e / b, capex: n * unit_price, density: e / t / n / WAFER_MM2, pue: PUE_LIQ, lat }
}
fn cost(r: &R, b: f64) -> (f64, f64) { let toks = b / r.t * UTIL; (r.capex / LIFE_S / toks * 1e6, r.ej * r.pue * KWH / 3.6e6 * 1e6) }
fn main() {
    let m = M { name: "MoE 1T/32B", total: 1000e9, active: 32e9, layers: 61.0, d: 7168.0, kv_div: 16.0 };
    let others = [M { name: "dense 70B", total: 70e9, active: 70e9, layers: 80.0, d: 8192.0, kv_div: 8.0 }, M { name: "MoE 671B/37B", total: 671e9, active: 37e9, layers: 61.0, d: 7168.0, kv_div: 16.0 }];
    let bits = 4.0; let b = 64.0; let bottom_up = WAFER_PRICE / (1.0 - SPARE) + SYS_HW;
    println!("MODEL, not a measurement. {} 4-bit, {} sequences, context {}. Latency model: {} phases per layer, {} ns per hop, tile {} mm2, link {} us (all ASSUMED).", m.name, b, L, PHASES, HOP_S * 1e9, TILE_MM2, LINK_S * 1e6);
    println!("{:<12} {:<26} {:>3} {:>11} {:>12} {:>9} {:>9} {:>9} {:>8} | {:>9} {:>9} {:>9}", "model", "machine", "n", "token lat ms", "tok/s/seq", "tok/s", "J/token", "power kW", "W/mm2", "$/Mtok c", "$/Mtok e", "$/Mtok");
    let show = |mm: &M, nm: &str, r: &R| { let (c, e) = cost(r, b); println!("{:<12} {:<26} {:>3.0} {:>11.3} {:>12.0} {:>9.0} {:>9.3} {:>9.1} {:>8.3} | {:>9.3} {:>9.3} {:>9.3}", mm.name, nm, r.n, r.lat * 1e3, 1.0 / r.lat, b / r.t, r.ej, r.p_w / 1e3, r.density, c, e, c + e); };
    let g = gpu(&m, bits, b, 350.0, 25000.0); let c = cb(&m, bits, b); let a = lw(&m, bits, b, E_HI, 1.6, bottom_up); let a_par = lw(&m, bits, b, E_HI, 1.6, CB_PRICE);
    show(&m, "GPU cluster (350 W, $25k)", &g); show(&m, "cited wafer system (ref)", &c); show(&m, "L-wafer A, cited price", &a_par); show(&m, "L-wafer A, bottom-up", &a);
    for o in others.iter() { let g = gpu(o, bits, b, 350.0, 25000.0); let a = lw(o, bits, b, E_HI, 1.6, bottom_up); show(o, "GPU cluster", &g); show(o, "L-wafer A, bottom-up", &a); }
    let gt = { let (x, y) = cost(&g, b); x + y };
    println!("\nHardware-cost threshold (I2'): the highest system hardware cost per wafer at which L-wafer A stays at or below 0.5x the GPU cluster, for each GPU assumption:");
    println!("{:>8} {:>8} | {:>10} {:>14} {:>14} {:>9}", "GPU W", "GPU $", "GPU $/Mtok", "max hardware $", "break-even $/wafer", "J2' ratio");
    let mut j2_ok = true; let mut thr_ok = true;
    for &w in &[100.0, 220.0, 350.0, 700.0] { for &p in &[15000.0, 25000.0, 40000.0] {
        let gg = gpu(&m, bits, b, w, p); let (gc, ge) = cost(&gg, b); let g_tot = gc + ge; let aa = lw(&m, bits, b, E_HI, 1.6, bottom_up); let (_, ae) = cost(&aa, b);
        let toks = b / aa.t * UTIL; let allow = (0.5 * g_tot - ae) / 1e6 * toks * LIFE_S / aa.n; let max_hw = allow - WAFER_PRICE / (1.0 - SPARE);
        let be = (g_tot - ae) / 1e6 * toks * LIFE_S / aa.n; let ratio = (gg.ej * gg.pue) / (aa.ej * aa.pue);
        println!("{:>8.0} {:>8.0} | {:>10.3} {:>14.0} {:>14.0} {:>8.1}x", w, p, g_tot, max_hw, be, ratio);
        if w >= 220.0 && ratio < 5.0 { j2_ok = false; } if w >= 220.0 && p >= 25000.0 && max_hw < SYS_HW { thr_ok = false; }
    } }
    // CALIBRATION against vendor-reported speeds (not a bar; added to check the latency model, vendor figures are launch-era Nov 2024 claims, 16-bit weights, per user):
    println!("\nCalibration of the latency model on the cited wafer system (16-bit weights, batch 1): vendor-reported per-user speed about 2,100 tokens/s for Llama 3.1 70B and 969 for 405B.");
    for (nm, mm) in [("dense 70B", &others[0]), ("dense 405B", &M { name: "dense 405B", total: 405e9, active: 405e9, layers: 126.0, d: 16384.0, kv_div: 8.0 })] {
        let r = cb(mm, 16.0, 1.0); println!("  {}: modelled {:.0} tokens/s per sequence on {:.0} wafers", nm, 1.0 / r.lat, r.n);
    }
    let (ac, ae) = cost(&a, b);
    println!("\nBAR RESULTS (pre-set, applied as written):");
    println!("L1 token latency {:.3} ms (needs <= 2 ms): {}   [step 3 assumed 0.5 ms; per-sequence speed {:.0} tokens/s]", a.lat * 1e3, if a.lat <= 2e-3 { "PASS" } else { "FAIL" }, 1.0 / a.lat);
    println!("I2' bottom-up ${:.3} per Mtok against GPU ${:.3} (needs <= ${:.3}): {}; hardware-cost threshold at the central GPU assumption (350 W, $25k): see table; threshold >= $150k across 220-700 W and >= $25k: {}", ac + ae, gt, 0.5 * gt, if ac + ae <= 0.5 * gt { "PASS" } else { "FAIL" }, if thr_ok { "PASS" } else { "FAIL" });
    println!("J2' facility energy ratio >= 5x for every GPU power 220-700 W: {}", if j2_ok { "PASS" } else { "FAIL" });
    println!("J1' heat density {:.3} W/mm2 (needs <= 1.0): {}", a.density, if a.density <= 1.0 { "PASS" } else { "FAIL" });
    let _ = (c.capex, WAFER_300);
}
