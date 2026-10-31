// 31 Oct 2026, MODEL (analytic capacity and energy model; every constant is an assumption or a cited figure, labelled below; nothing here is measured).
// New start, rows B and A of docs/gpu_workload_map.md: run EXISTING models (dense and mixture-of-experts, 16/8/4-bit weights) on a machine that keeps the weights in on-chip SRAM,
// and benchmark it against (1) a GPU cluster with HBM and (2) a Cerebras-class wafer (44 GB SRAM per wafer, CITED vendor figure). Written BEFORE the first run.
//
// PRE-SET BARS (written before running):
//   B1 capacity : an SRAM-heavy wafer in TODAY'S technology (project SRAM density, no new memory technology) holds at least 2x the 44 GB of a Cerebras WSE-3 at equal bits.
//   B2 energy   : on the 70B dense model and the 1T-parameter mixture-of-experts model, 4-bit weights, batch 1, energy per token at least 5x below the GPU cluster, using the
//                 PESSIMISTIC SRAM energy (2.78 pJ/bit). The mid value (1.0) and the optimistic value (0.495) are reported next to it, and the SRAM energy that WOULD give 5x is printed.
//   B3 vs Cerebras-class : at equal batch and the same SRAM energy constants, energy per token no worse, and at least 1.5x fewer wafers for the 1T mixture-of-experts model at 4-bit.
//   B4 speed    : at batch 1 the 70B dense model at 4-bit generates at least as many tokens per second per sequence as the GPU cluster.
// A row that misses its bar is reported as missed; no constant is changed after the run to rescue it.
// Build: rustc -O step2_wafer_sram_model.rs   Standard library only.
//
// Per step of a batch of B sequences (one token each):
//   weight bytes read = total_bytes * touched, touched = 1 for dense, 1-(1-active/total)^B for mixture-of-experts (independent routing, an approximation);
//   KV cache bytes = B * 2 * layers * (d / kv_div) * L * 2 (16-bit); multiply-adds = B * (active params + 2 * layers * d * L).
//   GPU (H100-class, ASSUMED from memory of the public spec: 80 GB HBM3, 3.35 TB/s, 495 TMAC/s; HBM energy 5.74 pJ/bit is the project value; idle floor 100 W per GPU ASSUMED, a loaded board draws more):
//        n = ceil(bytes / 72 GB); time = max(bytes/(BW n), macs/(PEAK n)); energy = bytes*8*E_HBM + macs*MAC + 100 W * n * time. Links between GPUs are NOT charged (favours the GPU).
//   Cerebras-class wafer (CITED vendor figures, secondary sources: 44 GB SRAM, 46,225 mm2, 21 PB/s on-die SRAM bandwidth, about 23 kW per system; the 62 PMAC/s is half the quoted 125 PFLOPs, ASSUMED):
//        same SRAM energy constants as ours (an assumption: same technology class); energy shown without static power ("dyn") and with the quoted 23 kW drawn during the step ("23kW", an upper figure).
//   L-wafer A (OUR OPTION, current technology): 80% of a 46,225 mm2 wafer is SRAM at the project's 341 mm2 per GB = 108 GB; bandwidth proportional to capacity (the same per-GB ports as the cited wafer);
//        compute 10 PMAC/s (ASSUMED); static = 0.5 W logic + leakage per GB (0.5 mid, 1.6 pessimistic of the project range 0.2 to 1.6). L-wafer B = A with two stacked memory layers (217 GB): an OPTION that needs
//        3D stacking, not available in the open flow. Wafer-to-wafer activation links charged at 10 pJ/bit (ASSUMED).
//   MAC energy by weight width (assumed, same on every machine except the GPU, which dequantises to 8-bit math): 16-bit 1.5 pJ, 8-bit 0.25, 4-bit 0.12.
const E_HBM: f64 = 5.74; const E_HI: f64 = 2.78; const E_MID: f64 = 1.0; const E_LO: f64 = 0.495; const E_LINK: f64 = 10.0;
const L: f64 = 4096.0;
const GPU_BW: f64 = 3.35e12; const GPU_PEAK: f64 = 495e12; const GPU_CAP: f64 = 72e9; const GPU_STATIC: f64 = 100.0;
const CB_CAP: f64 = 44e9; const CB_BW: f64 = 21e15; const CB_PEAK: f64 = 62e15; const CB_P: f64 = 23000.0; const WAFER_MM2: f64 = 46225.0;
const MM2_PER_GB: f64 = 341.0; const LW_PEAK: f64 = 10e15; const BW_PER_BYTE: f64 = 21e15 / 44e9;
fn gs() -> f64 { std::env::var("GPU_STATIC_W").ok().and_then(|v| v.parse().ok()).unwrap_or(GPU_STATIC) } // override for the sensitivity runs
fn mac_pj(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else if bits >= 8.0 { 0.25 } else { 0.12 } }
fn gpu_mac(bits: f64) -> f64 { if bits >= 16.0 { 1.5 } else { 0.25 } }
struct M { name: &'static str, total: f64, active: f64, layers: f64, d: f64, kv_div: f64 }
struct Step { bytes: f64, kv: f64, macs: f64, wtot: f64 }
fn step(m: &M, bits: f64, b: f64) -> Step {
    let wtot = m.total * bits / 8.0; let f = m.active / m.total; let touched = if f >= 0.999 { 1.0 } else { 1.0 - (1.0 - f).powf(b) };
    let kv = b * 2.0 * m.layers * (m.d / m.kv_div) * L * 2.0; let macs = b * (m.active + 2.0 * m.layers * m.d * L);
    Step { bytes: wtot * touched + kv, kv, macs, wtot }
}
// returns (joules per token, tokens per second per sequence, number of GPUs)
fn gpu(m: &M, bits: f64, b: f64) -> (f64, f64, f64) {
    let s = step(m, bits, b); let n = ((s.wtot + s.kv) / GPU_CAP).ceil().max(1.0);
    let t = (s.bytes / (GPU_BW * n)).max(s.macs / (GPU_PEAK * n));
    ((s.bytes * 8.0 * E_HBM * 1e-12 + s.macs * gpu_mac(bits) * 1e-12 + gs() * n * t) / b, 1.0 / t, n)
}
// a wafer machine: capacity per wafer, bandwidth per wafer, peak per wafer, static watts per wafer (function of capacity), SRAM energy
fn wafer(m: &M, bits: f64, b: f64, cap: f64, bw: f64, peak: f64, p_static: f64, e_sram: f64) -> (f64, f64, f64) {
    let s = step(m, bits, b); let n = ((s.wtot + s.kv) / cap).ceil().max(1.0);
    let t = (s.bytes / (bw * n)).max(s.macs / (peak * n));
    let link = (n - 1.0) * m.d * 2.0 * 8.0 * E_LINK * 1e-12 * b; // one activation crossing per wafer boundary per token step
    ((s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + p_static * n * t + link) / b, 1.0 / t, n)
}
fn lw(m: &M, bits: f64, b: f64, gb: f64, e_sram: f64, leak: f64) -> (f64, f64, f64) {
    wafer(m, bits, b, gb * 1e9, BW_PER_BYTE * gb * 1e9, LW_PEAK, 0.5 + leak * gb, e_sram)
}
fn main() {
    let models = [
        M { name: "dense 7B", total: 7e9, active: 7e9, layers: 32.0, d: 4096.0, kv_div: 4.0 },
        M { name: "dense 70B", total: 70e9, active: 70e9, layers: 80.0, d: 8192.0, kv_div: 8.0 },
        M { name: "dense 405B", total: 405e9, active: 405e9, layers: 126.0, d: 16384.0, kv_div: 8.0 },
        M { name: "MoE 671B/37B", total: 671e9, active: 37e9, layers: 61.0, d: 7168.0, kv_div: 16.0 },
        M { name: "MoE 1T/32B", total: 1000e9, active: 32e9, layers: 61.0, d: 7168.0, kv_div: 16.0 },
    ];
    let a_gb = 0.8 * WAFER_MM2 / MM2_PER_GB; let b_gb = 2.0 * a_gb;
    println!("MODEL, not a measurement. Context {} tokens. Architectures are stand-ins for the model classes (layer counts and widths from memory, not exact).", L);
    println!("Capacity: cited wafer {:.0} GB ({:.0} mm2); L-wafer A {:.1} GB (80% of the wafer at {} mm2/GB, today's technology) = {:.2}x; L-wafer B {:.1} GB (two stacked layers, an OPTION) = {:.2}x.", CB_CAP / 1e9, WAFER_MM2, a_gb, MM2_PER_GB, a_gb / 44.0, b_gb, b_gb / 44.0);
    println!("Cited wafer density implied: {:.2} Mbit/mm2 of whole wafer; project SRAM density {:.1} Mbit/mm2 -> the cited wafer spends about {:.0}% of its area on SRAM at that density (a derived figure, ASSUMED density).\n", 44e9 * 8.0 / 1e6 / WAFER_MM2, 8.59e9 / 1e6 / MM2_PER_GB, 44.0 * MM2_PER_GB / WAFER_MM2 * 100.0);
    println!("Parameters that fit in ONE wafer of SRAM (billions), by weight width:");
    println!("{:<22} {:>8} {:>8} {:>8}", "wafer", "16-bit", "8-bit", "4-bit");
    for (n, gb) in [("cited wafer (44 GB)", 44.0), ("L-wafer A", a_gb), ("L-wafer B (stacked)", b_gb)] { println!("{:<22} {:>8.1} {:>8.1} {:>8.1}", n, gb / 2.0, gb, gb * 2.0); }
    println!("\nEnergy per token in joules (J/tok) and speed (tok/s per sequence). GPU = H100-class cluster; CB = cited wafer(s), dyn = no static power, 23kW = quoted system power drawn during the step; LA = L-wafer A at SRAM energy hi/mid/lo.");
    println!("{:<13} {:>4} {:>3} | {:>3} {:>9} {:>7} | {:>3} {:>9} {:>9} | {:>3} {:>9} {:>9} {:>9} {:>7} | {:>7} {:>7} {:>7} | {:>9}", "model", "bits", "B", "gpu", "J/tok", "tok/s", "CBw", "dyn", "23kW", "LAw", "hi", "mid", "lo", "tok/s", "GPU/hi", "GPU/mid", "GPU/lo", "E* for 5x");
    let mut b2 = Vec::new(); let mut b3 = Vec::new(); let mut b4 = true;
    for m in &models {
        for &bits in &[16.0, 8.0, 4.0] {
            for &b in &[1.0, 32.0] {
                let (eg, tg, ng) = gpu(m, bits, b);
                let (ec, _, nc) = wafer(m, bits, b, CB_CAP, CB_BW, CB_PEAK, 0.0, E_HI);
                let (ec23, _, _) = wafer(m, bits, b, CB_CAP, CB_BW, CB_PEAK, CB_P, E_HI);
                let (ea_hi, ta, na) = lw(m, bits, b, a_gb, E_HI, 1.6); let (ea_mid, _, _) = lw(m, bits, b, a_gb, E_MID, 0.5); let (ea_lo, _, _) = lw(m, bits, b, a_gb, E_LO, 0.2);
                // E_sram that would give exactly 5x: energy is linear in e_sram; get the slope from two evaluations
                let (e1, _, _) = lw(m, bits, b, a_gb, 1.0, 1.6); let (e2, _, _) = lw(m, bits, b, a_gb, 2.0, 1.6); let slope = e2 - e1; let c0 = e1 - slope;
                let estar = (eg / 5.0 - c0) / slope;
                println!("{:<13} {:>4} {:>3} | {:>3.0} {:>9.3} {:>7.1} | {:>3.0} {:>9.3} {:>9.2} | {:>3.0} {:>9.3} {:>9.3} {:>9.3} {:>7.1} | {:>6.1}x {:>6.1}x {:>6.1}x | {:>9}", m.name, bits, b, ng, eg, tg, nc, ec, ec23, na, ea_hi, ea_mid, ea_lo, ta, eg / ea_hi, eg / ea_mid, eg / ea_lo, if estar > 0.0 { format!("{:.2} pJ", estar) } else { "never".to_string() });
                if bits == 4.0 && b == 1.0 && (m.name == "dense 70B" || m.name == "MoE 1T/32B") { b2.push((m.name, eg / ea_hi, eg / ea_mid, estar)); }
                if bits == 4.0 && b == 1.0 && m.name == "dense 70B" && ta < tg { b4 = false; }
                if bits == 4.0 && m.name == "MoE 1T/32B" { b3.push((b, ea_hi <= ec, nc, na)); }
            }
        }
    }
    println!("\nBAR RESULTS (pre-set, applied as written):");
    println!("B1 capacity: L-wafer A holds {:.2}x the cited wafer (needs >= 2x): {}   (an area-share choice at the project SRAM density; whether the rest of the wafer can carry the compute and routing is NOT shown by this model)", a_gb / 44.0, if a_gb / 44.0 >= 2.0 { "PASS" } else { "FAIL" });
    for (n, rhi, rmid, es) in &b2 { println!("B2 energy {}: ratio {:.1}x at the pessimistic 2.78 pJ/bit (needs >= 5x), {:.1}x at 1.0 pJ/bit; SRAM energy needed for 5x: {}: {}", n, rhi, rmid, if *es > 0.0 { format!("{:.2} pJ/bit", es) } else { "unreachable".to_string() }, if *rhi >= 5.0 { "PASS" } else { "FAIL" }); }
    for (b, ok, nc, na) in &b3 { println!("B3 vs cited wafer, MoE 1T at 4-bit, batch {}: energy no worse (same SRAM energy, L static included, cited dyn only) {}; wafers {} vs {} (needs cited >= 1.5x ours: {}): {}", b, if *ok { "yes" } else { "no" }, nc, na, nc / na, if *ok && nc / na >= 1.5 { "PASS" } else { "FAIL" }); }
    println!("B4 speed: 70B dense, 4-bit, batch 1, L-wafer A tok/s >= GPU cluster tok/s: {}", if b4 { "PASS" } else { "FAIL" });
}
