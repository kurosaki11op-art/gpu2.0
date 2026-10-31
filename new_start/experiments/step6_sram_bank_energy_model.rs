// 31 Oct 2026, MODEL (analytic bank-level SRAM read-energy and density model; nothing measured). Fix lever 2 of step5_worst_case_result.md: can a weight-stationary SRAM read cost 1.6 pJ/bit or less, all in?
// Written BEFORE the first run.
//
// MODEL: the energy to read one weight bit from its bank to the multiplier next to it =
//   (macro access energy per bit + fixed periphery overhead) + wire energy from the bank edge to the multiplier.
//   macro access energy per access = E_REF x sqrt(N / N_REF) x (w / W_REF)^0.7 ; per bit = that / w. (bitline and wordline length grow with sqrt of the bank bits; a wider access shares the decode; exponents ASSUMED)
//   E_REF = 3.89 pJ per access at N_REF = 563 kbit: ONE cited datapoint (a 3 nm dual-rail SRAM, access width not stated; W_REF = 64 bit ASSUMED); no other sourced figure was found.
//   overhead (decode, sense, timing, control) factor 1.3 ASSUMED. Wire: C_wire = 0.2 fF per um (textbook value, ASSUMED), V = 0.75 V, activity 0.5 -> 0.056 pJ per bit per mm; distance d from the bank to its multiplier.
//   Cross-check from memory (a widely quoted 45 nm table, NOT verified here): 8 KB 10 pJ, 32 KB 20 pJ, 1 MB 100 pJ per 64-bit read = 0.16, 0.31, 1.56 pJ/bit; this model at 45 nm-equivalent scaling is printed beside it.
//   Density: base 25.2 Mbit/mm2 (project, 341 mm2 per GB) at an array efficiency of 80% (a 1 MB bank); smaller banks lose efficiency to periphery: ASSUMED 50% at 32 KB, 65% at 128 KB, 75% at 512 KB, 80% at 1 MB, 85% at 4 MB.
// PRE-SET BARS:
//   S1: some design point (bank size, access width, distance) has all-in read energy <= 1.6 pJ/bit with area per GB at most 1.25x the project's 341 mm2 per GB.
//   S2: with that design point's energy and density, the worst corner of step 5 (GPU 100 W and $15k, latency x2.7) meets the energy bar W2 (facility energy >= 5x below the GPU) for the reticle-chip option.
//   S3 (robustness): the same design point still meets 1.6 pJ/bit with every model parameter at its pessimistic end: E_REF x2, overhead x1.6, wire 0.11 pJ/bit/mm, W_REF 32.
// Build: rustc -O step6_sram_bank_energy_model.rs   Standard library only.
const E_REF: f64 = 3.89; const N_REF: f64 = 563e3; const W_REF: f64 = 64.0; const OVH: f64 = 1.3; const WIRE: f64 = 0.056;
fn eff(n: f64) -> f64 { let kb = n / 8.0 / 1024.0; if kb <= 32.0 { 0.50 } else if kb <= 128.0 { 0.65 } else if kb <= 512.0 { 0.75 } else if kb <= 1024.0 { 0.80 } else { 0.85 } }
fn e_bit(n: f64, w: f64, d: f64, e_ref: f64, ovh: f64, wire: f64, w_ref: f64) -> f64 { (e_ref * (n / N_REF).sqrt() * (w / w_ref).powf(0.7) / w) * ovh + wire * d }
fn mm2_per_gb(n: f64) -> f64 { 341.0 * 0.8 / eff(n) }
fn main() {
    println!("MODEL, not a measurement. All-in read energy per weight bit (pJ/bit) and area per GB by bank size, access width, bank-to-multiplier distance.");
    println!("Cross-check at 45 nm-equivalent (E_REF x6.7, from the ratio of the quoted 1 MB figure to this model at 1 MB; a calibration, not an independent test): printed below.\n");
    println!("{:>9} {:>6} | {:>6} {:>8} {:>8} {:>8} | {:>9}", "bank", "width", "d mm", "pJ/bit", "pJ/bit", "pJ/bit", "mm2/GB");
    println!("{:>9} {:>6} | {:>6} {:>8} {:>8} {:>8} | {:>9}", "", "", "", "d=0.1", "d=0.5", "d=3", "");
    let banks = [16.0 * 8192.0, 32.0 * 8192.0, 128.0 * 8192.0, 512.0 * 8192.0, 1024.0 * 8192.0, 4096.0 * 8192.0];
    let mut best: Option<(f64, f64, f64, f64, f64)> = None; // (energy, n, w, d, mm2gb)
    for &n in &banks { for &w in &[32.0, 64.0, 128.0, 256.0] {
        println!("{:>7.0}KB {:>6.0} | {:>6} {:>8.3} {:>8.3} {:>8.3} | {:>9.0}", n / 8192.0, w, "", e_bit(n, w, 0.1, E_REF, OVH, WIRE, W_REF), e_bit(n, w, 0.5, E_REF, OVH, WIRE, W_REF), e_bit(n, w, 3.0, E_REF, OVH, WIRE, W_REF), mm2_per_gb(n));
        for &d in &[0.1, 0.5, 3.0] { let e = e_bit(n, w, d, E_REF, OVH, WIRE, W_REF); let a = mm2_per_gb(n);
            if a <= 341.0 * 1.25 && e <= 1.6 && best.map_or(true, |b| e < b.0) { best = Some((e, n, w, d, a)); } }
    } }
    println!("\n45 nm-equivalent cross-check (per 64-bit read, wire ignored): 8 KB {:.2} pJ/bit, 32 KB {:.2}, 1 MB {:.2}   (quoted from memory, unverified: 0.16, 0.31, 1.56)", e_bit(8.0 * 8192.0, 64.0, 0.0, E_REF * 6.7, OVH, WIRE, W_REF), e_bit(32.0 * 8192.0, 64.0, 0.0, E_REF * 6.7, OVH, WIRE, W_REF), e_bit(1024.0 * 8192.0, 64.0, 0.0, E_REF * 6.7, OVH, WIRE, W_REF));
    println!("\nBAR RESULTS (pre-set):");
    match best {
        Some((e, n, w, d, a)) => {
            println!("S1 PASS: best point within the area limit: bank {:.0} KB, width {:.0} bit, distance {:.1} mm -> {:.3} pJ/bit all in, {:.0} mm2 per GB ({:.2}x the project figure)", n / 8192.0, w, d, e, a, a / 341.0);
            let pess = e_bit(n, w, d, E_REF * 2.0, OVH * 1.6 / 1.3 * 1.3 / 1.3, 0.112, 32.0); let pess2 = e_bit(n, 32.0, d, E_REF * 2.0, 1.6, 0.112, 32.0);
            println!("S3 pessimistic ends (E_REF x2, overhead 1.6, wire 0.11 pJ/bit/mm, W_REF 32, width kept at {:.0} bit): {:.3} pJ/bit -> {}; same with the width cut to 32 bit: {:.3} pJ/bit", w, pess.max(e_bit(n, w, d, E_REF * 2.0, 1.6, 0.112, 32.0)), if e_bit(n, w, d, E_REF * 2.0, 1.6, 0.112, 32.0) <= 1.6 { "PASS" } else { "FAIL" }, pess2);
            println!("S2: feed {:.3} pJ/bit and {:.0} mm2 per GB to step 5 (see the result note).", e, a);
        }
        None => println!("S1 FAIL: no scanned point reaches 1.6 pJ/bit within 1.25x the project area per GB."),
    }
}
