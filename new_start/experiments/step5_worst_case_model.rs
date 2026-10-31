// 31 Oct 2026, MODEL (analytic; nothing measured). Rows I and J, "close = fix the failures" (founder, 31 Oct 2026). Written BEFORE the first run.
// Step 4 passed its bars at the CENTRAL assumptions only and left three outside numbers open. This step asks what happens in the WORST corner for our side, and lets BOTH machines choose their best batch
// (a bigger batch lowers cost per token on a GPU too), under a speed floor, so that the comparison is fair.
//
// CORNERS (ours is the pessimistic side in each): GPU decode power 100 W and price $15k; wafer latency 1.5x the calibrated model (factor 2.7 instead of 1.8); SRAM read 2.78 pJ/bit with leakage 1.6 W/GB;
//   wafer system priced at the cited $2.5M (no bottom-up discount); HBM energy 5.74 pJ/bit. CENTRAL corner: GPU 350 W, $25k, factor 1.8, wafer system at the bottom-up price $168,687.
// SERVICE FLOOR: at least 30 tokens per second per sequence; each machine picks the batch (64 to 1,024 sequences) with the lowest cost per million tokens that meets it.
// PRE-SET BARS, in the WORST corner: W1 cost per million tokens at most 0.5x the GPU cluster; W2 facility energy per token at least 5x below the GPU cluster.
// IF A BAR FAILS the output prints the lever that would fix it and the value needed (system price for W1; SRAM read energy for W2); a lever counts as a fix only if a design change (named in the result note) supports it.
// Build: rustc -O step5_worst_case_model.rs   Standard library only. Inputs, labels and sources: see step3_cost_power_result.md and step4_close_i_j_result.md.
const WAFER_PRICE: f64 = 18500.0; const WAFER_MM2: f64 = 46225.0;
// step 6 overrides (defaults = the step 5 values): MM2GB = area per GB of SRAM, SRAM_PJ = all-in read energy per bit
fn mm2gb() -> f64 { std::env::var("MM2GB").ok().and_then(|v| v.parse().ok()).unwrap_or(341.0) }
fn sram_pj() -> f64 { std::env::var("SRAM_PJ").ok().and_then(|v| v.parse().ok()).unwrap_or(2.78) } const TILE_MM2: f64 = 0.05; const SPARE: f64 = 0.01; const SYS_HW: f64 = 150000.0;
const E_HBM: f64 = 5.74; const L: f64 = 4096.0; const E_LINK: f64 = 10.0; const HOP_S: f64 = 1e-9; const PHASES: f64 = 6.0; const LINK_S: f64 = 1e-6;
const GPU_BW: f64 = 3.35e12; const GPU_PEAK: f64 = 495e12; const GPU_CAP: f64 = 72e9; const GPU_OVERHEAD: f64 = 1.5;
const LW_PEAK: f64 = 10e15; const BW_PER_BYTE: f64 = 21e15 / 44e9; const CB_PRICE: f64 = 2.5e6;
const KWH: f64 = 0.10; const LIFE_S: f64 = 4.0 * 365.0 * 86400.0; const UTIL: f64 = 0.5; const PUE_AIR: f64 = 1.4; const PUE_LIQ: f64 = 1.15; const SLA: f64 = 30.0;
fn mac_pj(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else if bits >= 8.0 { 0.25 } else { 0.12 } }
struct M { total: f64, active: f64, layers: f64, d: f64, kv_div: f64 }
struct S { wtot: f64, touched: f64, bytes: f64, kvseq: f64, macs: f64 }
fn step(m: &M, bits: f64, b: f64) -> S {
    let wtot = m.total * bits / 8.0; let f = m.active / m.total; let touched = if f >= 0.999 { 1.0 } else { 1.0 - (1.0 - f).powf(b) };
    let kvseq = 2.0 * m.layers * (m.d / m.kv_div) * L * 2.0; let macs = b * (m.active + 2.0 * m.layers * m.d * L);
    S { wtot, touched, bytes: wtot * touched + b * kvseq, kvseq, macs }
}
struct R { n: f64, lat: f64, t: f64, ej: f64, capex: f64, pue: f64, b: f64 } // lat: seconds per token per sequence; t: seconds per step of b tokens
fn units_for(s: &S, b: f64, cap: f64) -> f64 { ((s.wtot + b * s.kvseq) / cap).ceil().max(1.0) }
fn gpu(m: &M, bits: f64, b: f64, w: f64, price: f64) -> R {
    let price = std::env::var("GPU_PRICE_ABS").ok().and_then(|v| v.parse().ok()).unwrap_or(price); // step 7: price the GPU at its estimated manufacturing cost instead of its selling price
    let s = step(m, bits, b); let n = units_for(&s, b, GPU_CAP); let t = (s.bytes / (GPU_BW * n)).max(s.macs / (GPU_PEAK * n));
    let e = s.bytes * 8.0 * E_HBM * 1e-12 + s.macs * 0.25e-12 + w * n * t; R { n, lat: t, t, ej: e / b, capex: n * price * GPU_OVERHEAD, pue: PUE_AIR, b }
}
fn lw(m: &M, bits: f64, b: f64, e_sram: f64, leak: f64, unit_price: f64, scale: f64) -> R {
    let gb = 0.8 * WAFER_MM2 / mm2gb(); let cap = gb * 1e9; let s = step(m, bits, b); let n = units_for(&s, b, cap);
    let lpw = (m.layers / n).ceil(); let hops = (WAFER_MM2 / lpw).sqrt() / TILE_MM2.sqrt(); let q = (b / m.layers).max(1.0);
    let fabric = PHASES * hops * HOP_S; let comp = q * (m.active / m.layers + 2.0 * m.d * L) / (LW_PEAK / lpw);
    let read = (s.wtot * s.touched / m.layers + q * s.kvseq / m.layers) / (BW_PER_BYTE * cap / lpw);
    let lat = (m.layers * (fabric + comp + read) + (n - 1.0) * LINK_S) * scale; let t = b * lat / b.max(1.0); let thr_t = lat; let _ = thr_t;
    let link = (n - 1.0) * m.d * 2.0 * 8.0 * E_LINK * 1e-12 * b;
    let e = s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + (0.5 + leak * gb) * n * lat + link; R { n, lat, t: lat, ej: e / b, capex: n * unit_price, pue: PUE_LIQ, b }
}
// OPTION B (added after run 1 showed the wafer system price is the problem): many reticle-size SRAM chips in ordinary packages instead of one wafer-scale part.
// Chip 800 mm2 (an ordinary reticle-size die, ASSUMED), 80% SRAM (1.88 GB), die cost = N5 wafer $18,500 / 70 dies per wafer / 80% yield = $330 (dies per wafer and yield ASSUMED);
// package, board share, power and cooling per chip ASSUMED $1,000 (no source); inter-chip link 0.5 us per crossing and 10 pJ/bit (ASSUMED); compute per chip = the wafer's peak share by area.
fn chips(m: &M, bits: f64, b: f64, e_sram: f64, leak: f64, per_chip: f64, scale: f64) -> R {
    let gb = 0.8 * 800.0 / mm2gb(); let cap = gb * 1e9; let s = step(m, bits, b); let n = units_for(&s, b, cap); let cpl = (n / m.layers).ceil().max(1.0);
    let q = (b / m.layers).max(1.0); let peak = LW_PEAK * 800.0 / WAFER_MM2; let bwc = BW_PER_BYTE * cap;
    let fabric = PHASES * ((800.0f64).sqrt() / TILE_MM2.sqrt() * HOP_S + 0.5e-6 * cpl.log2().ceil().max(1.0));
    let comp = q * (m.active / m.layers + 2.0 * m.d * L) / (peak * cpl); let read = (s.wtot * s.touched / m.layers + q * s.kvseq / m.layers) / (bwc * cpl);
    let lat = (m.layers * (fabric + comp + read)) * scale; let link = m.layers * PHASES * (m.d * 2.0 * 8.0 * E_LINK * 1e-12) * cpl.log2().ceil().max(1.0) * b;
    let e = s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + (0.5 + leak * gb) * n * lat + link; R { n, lat, t: lat, ej: e / b, capex: n * per_chip, pue: PUE_LIQ, b }
}
// cost per million tokens: tokens per second = b / t_step where one step yields b tokens; for the wafer a step of b tokens takes lat (all sequences advance together through the pipeline)
fn cost(r: &R) -> (f64, f64) { let toks = r.b / r.t * UTIL; (r.capex / LIFE_S / toks * 1e6, r.ej * r.pue * KWH / 3.6e6 * 1e6) }
fn best(f: &dyn Fn(f64) -> R) -> (R, f64) { let mut bb: Option<(R, f64)> = None; for &b in &[64.0, 128.0, 256.0, 512.0, 1024.0] { let r = f(b); if 1.0 / r.lat < SLA { continue; } let (c, e) = cost(&r); let tot = c + e; if bb.as_ref().map_or(true, |x| tot < x.1) { bb = Some((r, tot)); } } bb.unwrap_or_else(|| { let r = f(64.0); let (c, e) = cost(&r); (r, c + e) }) }
fn main() {
    let m = M { total: 1000e9, active: 32e9, layers: 61.0, d: 7168.0, kv_div: 16.0 }; let bits = 4.0; let bu = WAFER_PRICE / (1.0 - SPARE) + SYS_HW;
    println!("MODEL, not a measurement. 1T MoE (32B active), 4-bit, context {}, speed floor {} tokens/s per sequence, each machine at its own best batch (64 to 1,024).", L, SLA);
    println!("{:<34} | {:>4} {:>5} {:>9} {:>9} {:>8} | {:>4} {:>5} {:>9} {:>9} {:>8} | {:>8} {:>8}", "corner", "gpuB", "gpus", "gpu $/Mt", "gpu J/tok", "tok/s/sq", "wafB", "wfrs", "wf $/Mt", "wf J/tok", "tok/s/sq", "cost x", "energy x");
    let corners: [(&str, f64, f64, f64, f64); 4] = [("central (350 W, $25k, x1.8, bottom-up)", 350.0, 25000.0, 1.8, bu), ("worst: 100 W, $15k, x2.7, cited price", 100.0, 15000.0, 2.7, CB_PRICE), ("worst but bottom-up price", 100.0, 15000.0, 2.7, bu), ("GPU 220 W, $25k, x2.7, cited price", 220.0, 25000.0, 2.7, CB_PRICE)];
    let mut worst = None;
    for (nm, w, p, sc, price) in corners.iter() {
        let (g, gt) = best(&|b| gpu(&m, bits, b, *w, *p)); let (a, at) = best(&|b| lw(&m, bits, b, sram_pj(), 1.6, *price, *sc));
        let ex = (g.ej * g.pue) / (a.ej * a.pue);
        println!("{:<34} | {:>4.0} {:>5.0} {:>9.3} {:>9.3} {:>8.0} | {:>4.0} {:>5.0} {:>9.3} {:>9.3} {:>8.0} | {:>7.2}x {:>7.1}x", nm, g.b, g.n, gt, g.ej, 1.0 / g.lat, a.b, a.n, at, a.ej, 1.0 / a.lat, gt / at, ex);
        if nm.starts_with("worst: ") { worst = Some((gt, at, ex, a.b, a.n, *w, *p, *sc)); }
    }
    println!("\nOPTION B: many reticle-size SRAM chips (die $330 + package, board share, power and cooling per chip as shown, ASSUMED), same corners and SRAM constants (2.78 pJ/bit, 1.6 W/GB):");
    println!("{:<34} {:>10} | {:>5} {:>6} {:>9} {:>9} {:>8} | {:>8} {:>8}", "corner", "$ per chip", "batch", "chips", "$/Mtok", "J/tok", "tok/s/sq", "cost x", "energy x");
    for (nm, w, p, sc, _) in corners.iter().take(2) {
        for &pc in &[1330.0, 2330.0, 5330.0] {
            let (g, gt) = best(&|b| gpu(&m, bits, b, *w, *p)); let (a, at) = best(&|b| chips(&m, bits, b, sram_pj(), 1.6, pc, *sc));
            println!("{:<34} {:>10.0} | {:>5.0} {:>6.0} {:>9.3} {:>9.3} {:>8.0} | {:>7.2}x {:>7.1}x", nm, pc, a.b, a.n, at, a.ej, 1.0 / a.lat, gt / at, (g.ej * g.pue) / (a.ej * a.pue));
        }
    }
    if let Some((gt, at, ex, ab, an, w, p, sc)) = worst {
        println!("\nBARS in the worst corner (pre-set): W1 cost at most 0.5x the GPU: ours is {:.2}x of GPU cost ({}) ; W2 facility energy at least 5x below: {:.1}x ({})", at / gt, if at <= 0.5 * gt { "PASS" } else { "FAIL" }, ex, if ex >= 5.0 { "PASS" } else { "FAIL" });
        // lever for W1: the system price that makes cost exactly 0.5x
        let (a0, _) = best(&|b| lw(&m, bits, b, sram_pj(), 1.6, 0.0, sc)); let (_, e0) = cost(&a0); let toks = a0.b / a0.t * UTIL; let allow = (0.5 * gt - e0) / 1e6 * toks * LIFE_S / a0.n;
        println!("LEVER W1: the wafer system price at which cost = 0.5x the GPU (worst corner): ${:.0} per wafer system ({:.0}% of the cited $2.5M); bottom-up estimate ${:.0}", allow, allow / CB_PRICE * 100.0, bu);
        // lever for W2: SRAM read energy and leakage that give 5x, scanning
        let mut found = None; for &e in &[2.78, 2.4, 2.0, 1.6, 1.2, 1.0, 0.8, 0.495] { for &lk in &[1.6, 0.5, 0.2] { let (a, _) = best(&|b| lw(&m, bits, b, e, lk, CB_PRICE, sc)); let (g, _) = best(&|b| gpu(&m, bits, b, w, p)); if found.is_none() && (g.ej * g.pue) / (a.ej * a.pue) >= 5.0 { found = Some((e, lk, (g.ej * g.pue) / (a.ej * a.pue))); } } }
        match found { Some((e, lk, r)) => println!("LEVER W2: first scanned setting reaching 5x: SRAM read {:.2} pJ/bit with leakage {:.1} W/GB -> {:.1}x (needs a bank-level design that delivers it; the central project range is 0.495 to 2.78 pJ/bit)", e, lk, r), None => println!("LEVER W2: no scanned SRAM setting reaches 5x here") }
        let _ = (ab, an);
    }
}
