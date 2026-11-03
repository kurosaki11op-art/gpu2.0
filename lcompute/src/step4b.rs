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
    let q1 = good == tot; println!("Q1 {}/{} shapes bit-identical: {}", good, tot, if q1 { "PASS" } else { "FAIL" });
    // information only: CPU back end speed of both kernels at 512^3 (the register-blocked kernel needs many more registers per thread, which the lockstep CPU executor stores per lane)
    let n = 512usize; let spec = || vec![Sp::B(crate::rnd(n * n, 3)), Sp::B(crate::rnd(n * n, 4)), Sp::B(vec![0f32; n * n]), Sp::I(n as i32), Sp::I(n as i32), Sp::I(n as i32)];
    let mut tt = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kt, dim(n / 16, n / 16, 1), dim(16, 16, 1), &spec()); tt = tt.min(t.elapsed().as_secs_f64()); }
    let mut tr = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, &kr, dim(n / 64, n / 64, 1), dim(16, 16, 1), &spec()); tr = tr.min(t.elapsed().as_secs_f64()); }
    println!("  CPU fast back end 512^3 (information only): matmul_tiled {:.3} s, matmul_reg {:.3} s", tt, tr);
    q1
}
