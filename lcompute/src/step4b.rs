// Step 4b tests (bars Q1 and the CPU part of Q4 in docs/ROADMAP.md): the register-blocked matmul gives the same bits as the plain tiled one.
use crate::interp::dim;
use crate::step3::{run_on, Sp};
use std::time::Instant;

pub fn run() -> bool {
    println!("\nSTEP 4b: register-blocked matmul (matmul_reg) against matmul_tiled");
    let (kt, kr) = (crate::matmul_tiled(), crate::matmul_reg()); let (mut good, mut tot) = (0, 0);
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (64, 64, 64), (100, 50, 70), (33, 129, 17), (128, 128, 128), (65, 17, 130), (1, 16, 64)] {
        let spec = || vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
        let (r0, o0) = run_on(false, &kt, dim((n + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), &spec());
        let (r1, o1) = run_on(false, &kr, dim((n + 63) / 64, (m + 63) / 64, 1), dim(16, 16, 1), &spec());
        let (r2, o2) = run_on(true, &kr, dim((n + 63) / 64, (m + 63) / 64, 1), dim(16, 16, 1), &spec());
        let same = |a: &Vec<Vec<f32>>, b: &Vec<Vec<f32>>| a[2].iter().zip(&b[2]).all(|(x, y)| x.to_bits() == y.to_bits());
        let ok = r0.is_ok() && r1.is_ok() && r2.is_ok() && same(&o0, &o1) && same(&o0, &o2); tot += 1; good += ok as i32;
        println!("  Q1 {}x{}x{}: interpreter(reg) == interpreter(tiled) {}, fast(reg) == interpreter(tiled) {}  {}", m, k, n, same(&o0, &o1), same(&o0, &o2), if ok { "ok" } else { "FAIL" });
    }
    // Q4 correctness on the CPU: the fused kernel has its own bits, so it is checked against its own reference (the interpreter) and against a float64 sum
    let (mut fg, mut ft, mut fr) = (0, 0, 0);
    for (kf, bt) in [(crate::matmul_fma(), 64usize), (crate::matmul_fma4(), 64), (crate::matmul_fma8(), 128)] { for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (100, 50, 70), (128, 128, 128), (65, 17, 130)] {
        let (a, b) = (crate::rnd(m * k, 3), crate::rnd(k * n, 4)); let spec = || vec![Sp::B(a.clone()), Sp::B(b.clone()), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
        let g = dim((n + bt - 1) / bt, (m + bt - 1) / bt, 1);
        let (r1, o1) = run_on(false, &kf, g, dim(16, 16, 1), &spec()); let (r2, o2) = run_on(true, &kf, g, dim(16, 16, 1), &spec());
        let same = o1[2].iter().zip(&o2[2]).all(|(x, y)| x.to_bits() == y.to_bits());
        let mut e = 0f64; let mut ratio = 0f64;
        for i in 0..m { for j in 0..n { let (mut s, mut sa) = (0f64, 0f64); for kk in 0..k { let tm_ = a[i * k + kk] as f64 * b[kk * n + j] as f64; s += tm_; sa += tm_.abs(); }
            e = e.max(crate::relerr(o1[2][i * n + j], s)); ratio = ratio.max((o1[2][i * n + j] as f64 - s).abs() / (k as f64 * 6e-8 * sa).max(1e-30)); } }
        let ok_first = r1.is_ok() && r2.is_ok() && same && e <= 1e-5; let ok_rule = r1.is_ok() && r2.is_ok() && same && ratio <= 1.0; ft += 1; fg += ok_first as i32; fr += ok_rule as i32;
        println!("  Q4/Q5 {} {}x{}x{}: fast == interpreter {}, max relative error vs float64 {:.1e} (bar as first written 1e-5: {}), {:.3} of the rounding bound (step 1b rule: {})", kf.name, m, k, n, same, e, if ok_first { "ok" } else { "FAIL" }, ratio, if ok_rule { "ok" } else { "FAIL" });
    } }
    println!("Q4/Q5 CPU part (3 fused kernels), bar as first written (1e-5): {}/{} {}; re-specified with the step 1b rule: {}/{} {}", fg, ft, if fg == ft { "PASS" } else { "FAIL" }, fr, ft, if fr == ft { "PASS" } else { "FAIL" });
    // Q6a: the double-buffered / other-shaped variants must give the same bits as matmul_fma8 (same sequential fused sum over k) and equal their own interpreter run
    let (mut vg, mut vt) = (0, 0); let k8 = crate::matmul_fma8();
    for (kv, bm, bn) in [(crate::matmul_fma8db(), 128usize, 128usize), (crate::matmul_fma8x4(), 128, 64), (crate::matmul_fma8x4db(), 128, 64), (crate::matmul_fma8k32(), 128, 128)] {
        for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (100, 50, 70), (128, 128, 128), (65, 17, 130), (130, 70, 200)] {
            let spec = || vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
            let (r0, o0) = run_on(false, &k8, dim((n + 127) / 128, (m + 127) / 128, 1), dim(16, 16, 1), &spec());
            let g = dim((n + bn - 1) / bn, (m + bm - 1) / bm, 1); let (r1, o1) = run_on(false, &kv, g, dim(16, 16, 1), &spec()); let (r2, o2) = run_on(true, &kv, g, dim(16, 16, 1), &spec());
            let same = |a: &Vec<Vec<f32>>, b: &Vec<Vec<f32>>| a[2].iter().zip(&b[2]).all(|(x, y)| x.to_bits() == y.to_bits());
            let ok = r0.is_ok() && r1.is_ok() && r2.is_ok() && same(&o0, &o1) && same(&o1, &o2); vt += 1; vg += ok as i32;
            if !ok { println!("  Q6a {} {}x{}x{}: == matmul_fma8 {}, fast == interpreter {}  FAIL", kv.name, m, k, n, same(&o0, &o1), same(&o1, &o2)); }
        }
    }
    println!("Q6a (4 new kernels, 6 shapes each): {}/{} bit-identical to matmul_fma8 and to their own interpreter run: {}", vg, vt, if vg == vt { "PASS" } else { "FAIL" });
    let q1 = good == tot; println!("Q1 {}/{} shapes bit-identical: {}", good, tot, if q1 { "PASS" } else { "FAIL" });
    // information only: CPU back end speed of both kernels at 512^3 (the register-blocked kernel needs many more registers per thread, which the lockstep CPU executor stores per lane)
    let n = 512usize; let spec = || vec![Sp::B(crate::rnd(n * n, 3)), Sp::B(crate::rnd(n * n, 4)), Sp::B(vec![0f32; n * n]), Sp::I(n as i32), Sp::I(n as i32), Sp::I(n as i32)];
    let mut tt = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kt, dim(n / 16, n / 16, 1), dim(16, 16, 1), &spec()); tt = tt.min(t.elapsed().as_secs_f64()); }
    let mut tr = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kr, dim(n / 64, n / 64, 1), dim(16, 16, 1), &spec()); tr = tr.min(t.elapsed().as_secs_f64()); }
    println!("  CPU fast back end 512^3 (information only): matmul_tiled {:.3} s, matmul_reg {:.3} s", tt, tr);
    q1
}
