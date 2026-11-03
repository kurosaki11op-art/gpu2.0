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
    let kf = crate::matmul_fma(); let (mut fg, mut ft) = (0, 0);
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (100, 50, 70), (128, 128, 128), (65, 17, 130)] {
        let (a, b) = (crate::rnd(m * k, 3), crate::rnd(k * n, 4)); let spec = || vec![Sp::B(a.clone()), Sp::B(b.clone()), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
        let g = dim((n + 63) / 64, (m + 63) / 64, 1);
        let (r1, o1) = run_on(false, &kf, g, dim(16, 16, 1), &spec()); let (r2, o2) = run_on(true, &kf, g, dim(16, 16, 1), &spec());
        let same = o1[2].iter().zip(&o2[2]).all(|(x, y)| x.to_bits() == y.to_bits());
        let mut e = 0f64; for i in 0..m { for j in 0..n { let mut s = 0f64; for kk in 0..k { s += a[i * k + kk] as f64 * b[kk * n + j] as f64; } e = e.max(crate::relerr(o1[2][i * n + j], s)); } }
        let ok = r1.is_ok() && r2.is_ok() && same && e <= 1e-5; ft += 1; fg += ok as i32;
        println!("  Q4 matmul_fma {}x{}x{}: fast == interpreter {}, max relative error vs float64 {:.1e}  {}", m, k, n, same, e, if ok { "ok" } else { "FAIL" });
    }
    println!("Q4 CPU part: {}/{} shapes: {}", fg, ft, if fg == ft { "PASS" } else { "FAIL" });
    let q1 = good == tot; println!("Q1 {}/{} shapes bit-identical: {}", good, tot, if q1 { "PASS" } else { "FAIL" });
    // information only: CPU back end speed of both kernels at 512^3 (the register-blocked kernel needs many more registers per thread, which the lockstep CPU executor stores per lane)
    let n = 512usize; let spec = || vec![Sp::B(crate::rnd(n * n, 3)), Sp::B(crate::rnd(n * n, 4)), Sp::B(vec![0f32; n * n]), Sp::I(n as i32), Sp::I(n as i32), Sp::I(n as i32)];
    let mut tt = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kt, dim(n / 16, n / 16, 1), dim(16, 16, 1), &spec()); tt = tt.min(t.elapsed().as_secs_f64()); }
    let mut tr = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kr, dim(n / 64, n / 64, 1), dim(16, 16, 1), &spec()); tr = tr.min(t.elapsed().as_secs_f64()); }
    println!("  CPU fast back end 512^3 (information only): matmul_tiled {:.3} s, matmul_reg {:.3} s", tt, tr);
    q1
}
