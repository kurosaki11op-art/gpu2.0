// 31 Oct 2026, MODEL (analytic cost, power and heat model; nothing here is measured). Extends step2_wafer_sram_model.rs with the three things that model left out: cost, yield/redundancy and power density.
// Rows I and J of docs/gpu_workload_map.md. Written BEFORE the first run.
//
// QUESTION (founder): if an SRAM-heavy wafer holds more memory than a Cerebras-class wafer, why has nobody done it - is it cost, yield, power, heat? And can it be cheaper per token and cooler?
//
// PRE-SET BARS (applied as written; no constant is changed after the run to rescue a bar):
//   I1: serving the 1T mixture-of-experts model at 4-bit, 64 sequences, context 4,096: L-wafer A priced at PARITY with the cited wafer system ($2.5M each, a third-party estimate) costs no more per million tokens than a GPU cluster.
//   I2: the same with a BOTTOM-UP price (wafer silicon + $150k assumed system hardware, no margin, no development cost): at most 0.5x the GPU cluster cost per million tokens.
//   I3: the system price at which L-wafer A equals the GPU cluster per million tokens is printed (the break-even), so the answer is a number, not a yes or no.
//   J1: heat density of L-wafer A while serving (watts per mm2 of silicon) at most 1.0 W/mm2, the level an air-cooled GPU reaches (about 0.86 W/mm2 for a 700 W, 814 mm2 chip); above that needs liquid cooling.
//   J2: facility energy per token (IT energy x cooling overhead) at least 5x below the GPU cluster at the pessimistic SRAM energy (2.78 pJ/bit).
// Build: rustc -O step3_cost_power_model.rs   Standard library only.
//
// INPUTS and their labels:
//   N5 wafer price about $17,000 (CSET model of 2020) to $18,500 (average of a 2026 table, range $16,000 to $21,300): THIRD-PARTY ESTIMATES. A 300 mm wafer is 70,686 mm2.
//   HBM3E price $12 to $17 per GB (trade-press, analyst estimates; the Stanford dataset says HBM prices are modelled): THIRD-PARTY ESTIMATES. Not used in the cluster cost, which is priced per GPU.
//   Cerebras CS-3 system $2 to $3 million (one third-party estimate; Cerebras does not publish prices): THIRD-PARTY ESTIMATE. About 23 kW per system (vendor claim, sources disagree: 23 or 27 kW).
//   GPU H100-class price $25,000 and host/network overhead 1.5x: ASSUMED (no source found in this session). GPU board power while decoding: ASSUMED 350 W (the step-2 sensitivity ran 100 to 700 W); set GPU_W to change.
//   Electricity $0.10 per kWh, life 4 years, utilisation 50% on both machines: ASSUMED. Cooling overhead (PUE) 1.4 air-cooled GPU hall, 1.15 liquid-cooled wafer system: ASSUMED.
//   Defect density 0.1 per cm2 (N5-class, ASSUMED); tile (core plus local SRAM) 0.05 mm2 (46,225 mm2 / 900,000 cores, derived from the cited figures); spare area 1% (ASSUMED); no clustered defects modelled.
//   SRAM 341 mm2 per GB, read energy 0.495 / 1.0 / 2.78 pJ/bit, static 0.5 W + 0.2 / 0.5 / 1.6 W per GB: project values (step 2).
const WAFER_300: f64 = 70686.0; const WAFER_PRICE: f64 = 18500.0; const WAFER_MM2: f64 = 46225.0; const MM2_PER_GB: f64 = 341.0;
const E_HBM: f64 = 5.74; const E_HI: f64 = 2.78; const L: f64 = 4096.0; const E_LINK: f64 = 10.0;
const GPU_BW: f64 = 3.35e12; const GPU_PEAK: f64 = 495e12; const GPU_CAP: f64 = 72e9; const GPU_PRICE: f64 = 25000.0; const GPU_OVERHEAD: f64 = 1.5; const GPU_MM2: f64 = 814.0;
const CB_CAP: f64 = 44e9; const CB_BW: f64 = 21e15; const CB_PEAK: f64 = 62e15; const CB_P: f64 = 23000.0; const CB_PRICE: f64 = 2.5e6;
const LW_PEAK: f64 = 10e15; const BW_PER_BYTE: f64 = 21e15 / 44e9; const SYS_HW: f64 = 150000.0;
const KWH: f64 = 0.10; const LIFE_S: f64 = 4.0 * 365.0 * 86400.0; const UTIL: f64 = 0.5; const PUE_AIR: f64 = 1.4; const PUE_LIQ: f64 = 1.15;
const D0_PER_MM2: f64 = 0.1 / 100.0; const TILE_MM2: f64 = 0.05; const SPARE: f64 = 0.01;
fn gpu_w() -> f64 { std::env::var("GPU_W").ok().and_then(|v| v.parse().ok()).unwrap_or(350.0) }
// per-step latency floor of a distributed SRAM machine (layer-to-layer synchronisation across the wafer, ASSUMED 0.5 ms; env T_MIN_MS). Added after run 1 (step3_run1_no_latency_floor.log) showed throughput at the bandwidth bound, over 10,000 tokens/s per sequence, which no layered model reaches; it makes the SRAM machines worse, not better.
fn tmin() -> f64 { std::env::var("T_MIN_MS").ok().and_then(|v| v.parse::<f64>().ok()).unwrap_or(0.5) * 1e-3 }
fn mac_pj(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else if bits >= 8.0 { 0.25 } else { 0.12 } }
struct M { name: &'static str, total: f64, active: f64, layers: f64, d: f64, kv_div: f64 }
struct S { wtot: f64, bytes: f64, kvseq: f64, macs: f64 }
fn step(m: &M, bits: f64, b: f64) -> S {
    let wtot = m.total * bits / 8.0; let f = m.active / m.total; let touched = if f >= 0.999 { 1.0 } else { 1.0 - (1.0 - f).powf(b) };
    let kvseq = 2.0 * m.layers * (m.d / m.kv_div) * L * 2.0; let macs = b * (m.active + 2.0 * m.layers * m.d * L);
    S { wtot, bytes: wtot * touched + b * kvseq, kvseq, macs }
}
struct R { n: f64, t: f64, p_w: f64, ej: f64, capex: f64, density: f64, pue: f64 } // units, step seconds, system watts, joules per token (IT), dollars, W per mm2 of silicon, cooling overhead
fn units_for(s: &S, b: f64, cap: f64) -> f64 { ((s.wtot + b * s.kvseq) / cap).ceil().max(1.0) }
fn gpu(m: &M, bits: f64, b: f64) -> R {
    let s = step(m, bits, b); let n = units_for(&s, b, GPU_CAP); let t = (s.bytes / (GPU_BW * n)).max(s.macs / (GPU_PEAK * n));
    let dyn_j = s.bytes * 8.0 * E_HBM * 1e-12 + s.macs * 0.25e-12; let e = dyn_j + gpu_w() * n * t; // board power during decode (ASSUMED) on top of the dynamic energy
    R { n, t, p_w: e / t, ej: e / b, capex: n * GPU_PRICE * GPU_OVERHEAD, density: e / t / n / GPU_MM2, pue: PUE_AIR }
}
fn cb(m: &M, bits: f64, b: f64) -> R {
    let s = step(m, bits, b); let n = units_for(&s, b, CB_CAP); let t = (s.bytes / (CB_BW * n)).max(s.macs / (CB_PEAK * n)).max(tmin());
    let dyn_j = s.bytes * 8.0 * E_HI * 1e-12 + s.macs * mac_pj(bits) * 1e-12; let e = dyn_j.max(CB_P * n * t); // the quoted system power drawn throughout the step (an upper figure)
    R { n, t, p_w: e / t, ej: e / b, capex: n * CB_PRICE, density: e / t / n / WAFER_MM2, pue: PUE_LIQ }
}
fn lw(m: &M, bits: f64, b: f64, e_sram: f64, leak: f64, unit_price: f64) -> R {
    let gb = 0.8 * WAFER_MM2 / MM2_PER_GB; let cap = gb * 1e9; let s = step(m, bits, b); let n = units_for(&s, b, cap);
    let t = (s.bytes / (BW_PER_BYTE * cap * n)).max(s.macs / (LW_PEAK * n)).max(tmin()); let link = (n - 1.0) * m.d * 2.0 * 8.0 * E_LINK * 1e-12 * b;
    let e = s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + (0.5 + leak * gb) * n * t + link;
    R { n, t, p_w: e / t, ej: e / b, capex: n * unit_price, density: e / t / n / WAFER_MM2, pue: PUE_LIQ }
}
// dollars per million tokens: capital over the machine's life at the given utilisation, and energy including cooling
fn cost(r: &R, b: f64) -> (f64, f64) {
    let toks = b / r.t * UTIL; (r.capex / LIFE_S / toks * 1e6, r.ej * r.pue * KWH / 3.6e6 * 1e6)
}
fn main() {
    let models = [
        M { name: "dense 70B", total: 70e9, active: 70e9, layers: 80.0, d: 8192.0, kv_div: 8.0 },
        M { name: "MoE 671B/37B", total: 671e9, active: 37e9, layers: 61.0, d: 7168.0, kv_div: 16.0 },
        M { name: "MoE 1T/32B", total: 1000e9, active: 32e9, layers: 61.0, d: 7168.0, kv_div: 16.0 },
    ];
    let bits = 4.0; let b = 64.0;
    let silicon = WAFER_PRICE; let bottom_up = silicon / (1.0 - SPARE) + SYS_HW;
    println!("MODEL, not a measurement. 4-bit weights, {} sequences, context {}. GPU board power while decoding {} W (ASSUMED, env GPU_W). Cooling overhead: GPU hall {} (air), wafer systems {} (liquid), both ASSUMED. Electricity ${}/kWh, life 4 years, utilisation {:.0}% (ASSUMED).", b, L, gpu_w(), PUE_AIR, PUE_LIQ, KWH, UTIL * 100.0);
    // yield: expected defects per wafer and the share of tiles lost, with the spare area as redundancy
    let defects = WAFER_MM2 * D0_PER_MM2; let lost = defects * TILE_MM2 / WAFER_MM2;
    println!("Yield (ASSUMED defect density 0.1 per cm2): {:.0} expected defects on the {:.0} mm2 wafer; each kills one {:.2} mm2 tile (derived from the cited 900,000 cores), so {:.4}% of the tiles are lost against {:.0}% spare area -> redundancy covers the point defects by a wide margin; clustered defects, the periphery and the fabric are NOT modelled.", defects, WAFER_MM2, TILE_MM2, lost * 100.0, SPARE * 100.0);
    println!("Prices: silicon of one wafer-scale part ${:.0} (N5 wafer ${:.0}, a 300 mm wafer holds {:.0} mm2); L-wafer A bottom-up ${:.0} (silicon / (1 - spare) + ${:.0} assumed system hardware); cited system ${:.0}.", silicon, WAFER_PRICE, WAFER_300, bottom_up, SYS_HW, CB_PRICE);
    let gb = 0.8 * WAFER_MM2 / MM2_PER_GB;
    println!("Raw silicon cost per GB of SRAM on L-wafer A: ${:.0} per GB at the whole-wafer price (341 mm2 per GB at ${:.2} per mm2); the project cost model says $174 to $223 per GB; HBM3E sells for $12 to $17 per GB (price, not cost).\n", silicon / WAFER_300 * MM2_PER_GB, silicon / WAFER_300);
    println!("{:<13} {:<24} {:>4} {:>10} {:>9} {:>9} {:>8} {:>9} | {:>8} {:>8} {:>9}", "model", "machine", "n", "capex $M", "J/token", "power kW", "W/mm2", "tok/s", "$/Mtok cap", "$/Mtok en", "$/Mtok");
    let mut i1 = None; let mut i2 = None; let mut i3 = None; let mut j1 = None; let mut j2 = None;
    for m in &models {
        let g = gpu(m, bits, b); let c = cb(m, bits, b);
        let a_par = lw(m, bits, b, E_HI, 1.6, CB_PRICE); let a_bu = lw(m, bits, b, E_HI, 1.6, bottom_up); let a_mid = lw(m, bits, b, 1.0, 0.5, bottom_up);
        let rows: [(&str, &R); 5] = [("GPU cluster (H100-class)", &g), ("cited wafer system", &c), ("L-wafer A, cited price", &a_par), ("L-wafer A, bottom-up", &a_bu), ("L-wafer A, bottom-up, 1.0pJ", &a_mid)];
        for (nm, r) in rows.iter() {
            let (cc, ce) = cost(r, b); println!("{:<13} {:<24} {:>4.0} {:>10.2} {:>9.3} {:>9.1} {:>8.3} {:>9.0} | {:>8.3} {:>8.3} {:>9.3}", m.name, nm, r.n, r.capex / 1e6, r.ej, r.p_w / 1e3, r.density, b / r.t * UTIL, cc, ce, cc + ce);
        }
        let gtot = { let (x, y) = cost(&g, b); x + y };
        if m.name == "MoE 1T/32B" {
            let (pc, pe) = cost(&a_par, b); let (bc, be) = cost(&a_bu, b);
            i1 = Some((pc + pe, gtot)); i2 = Some((bc + be, gtot));
            // break-even unit price: capex needed so that capital + energy equals the GPU total; solve in dollars per wafer system
            let toks = b / a_bu.t * UTIL; let cap_allow = (gtot - be) / 1e6 * toks * LIFE_S; i3 = Some(cap_allow / a_bu.n);
            j1 = Some(a_bu.density); j2 = Some((g.ej * g.pue) / (lw(m, bits, b, E_HI, 1.6, bottom_up).ej * PUE_LIQ));
        }
        println!();
    }
    println!("BAR RESULTS (pre-set, applied as written; MoE 1T/32B, 4-bit, 64 sequences):");
    if let Some((a, g)) = i1 { println!("I1 L-wafer A at the cited price: ${:.2} per Mtok against GPU ${:.3} (needs <= GPU): {}", a, g, if a <= g { "PASS" } else { "FAIL" }); }
    if let Some((a, g)) = i2 { println!("I2 L-wafer A bottom-up: ${:.3} per Mtok against GPU ${:.3} (needs <= 0.5x = ${:.3}): {}", a, g, 0.5 * g, if a <= 0.5 * g { "PASS" } else { "FAIL" }); }
    if let Some(p) = i3 { println!("I3 break-even price per wafer system (bottom-up energy): ${:.0}  ({:.1}% of the cited ${:.0}; bottom-up estimate ${:.0})", p, p / CB_PRICE * 100.0, CB_PRICE, bottom_up); }
    if let Some(d) = j1 { println!("J1 heat density while serving: {:.3} W/mm2 (needs <= 1.0): {}  (a wafer-scale part also needs the heat carried out of a 46,225 mm2 plate, which no air heatsink does; that is a cooling-system cost, not shown here)", d, if d <= 1.0 { "PASS" } else { "FAIL" }); }
    if let Some(r) = j2 { println!("J2 facility energy per token, GPU / L-wafer A (pessimistic SRAM, cooling overheads included): {:.1}x (needs >= 5x): {}", r, if r >= 5.0 { "PASS" } else { "FAIL" }); }
    let _ = gb;
}
