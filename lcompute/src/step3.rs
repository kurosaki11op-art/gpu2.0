// Step 3 tests (bars C1 to C5 in docs/ROADMAP.md): the fast lockstep back end against the reference interpreter.
use crate::interp::{self, dim, Arg, Buf, Dim3};
use crate::ir::Kernel;
use std::time::Instant;

pub(crate) enum Sp { B(Vec<f32>), I(i32) }

pub(crate) fn run_on(fast: bool, k: &Kernel, grid: Dim3, block: Dim3, spec: &[Sp]) -> (Result<(), String>, Vec<Vec<f32>>) {
    let mut bufs: Vec<Vec<f32>> = spec.iter().filter_map(|s| if let Sp::B(v) = s { Some(v.clone()) } else { None }).collect();
    let mut args = Vec::new(); let mut bi = 0;
    for s in spec { match s { Sp::B(_) => { args.push(Arg::Buf(Buf { ptr: bufs[bi].as_mut_ptr(), len: bufs[bi].len() })); bi += 1; } Sp::I(v) => args.push(Arg::I32(*v)) } }
    let r = if fast { crate::fast::launch(k, grid, block, &args) } else { interp::launch(k, grid, block, &args) };
    (r, bufs)
}
// C1/C2 helper: same launch on both back ends, returns (identical, note)
fn same(k: &Kernel, grid: Dim3, block: Dim3, spec: &[Sp]) -> (bool, String) {
    let (ri, bi) = run_on(false, k, grid, block, spec); let (rf, bf) = run_on(true, k, grid, block, spec);
    if ri.is_err() || rf.is_err() { return (false, format!("interp {:?} / fast {:?}", ri, rf)); }
    for (x, y) in bi.iter().zip(&bf) { if x.iter().zip(y).any(|(a, b)| a.to_bits() != b.to_bits()) { return (false, "outputs differ".into()); } }
    (true, String::new())
}

pub fn prof() {
    if std::env::var("LC_RANGE2").is_ok() { let mut b = crate::builder::B::new("loop"); b.launch_bounds(16, 1, 1); let sh = b.shared(16); let z = b.ci(0); let n = b.ci(16); b.for_range(z, n, 1, |b, i| { let _v = b.load_s(sh, i); }); let k = b.finish(); for (i, ins) in k.code.iter().enumerate() { println!("{:2} {:?}", i, ins); } println!("{:?}", crate::range::analyse(&k)); return; }
    if std::env::var("LC_RANGE").is_ok() { let k = if std::env::var("LC_RANGE").unwrap() == "db" { crate::matmul_fma8db() } else { crate::matmul_fma8x4() }; let (safe, det) = crate::range::analyse(&k); for (i, lo, hi, len) in det { println!("pc {:3} {:?} index [{}, {}] of {} {}", i, if let crate::ir::Inst::LdS(..) = k.code[i] { "LdS" } else { "StS" }, lo, hi, len, if safe[i] { "proved" } else { "NOT proved" }); } return; }
    if std::env::var("LC_DUMP").is_ok() { for (i, ins) in crate::opt::optimise(&crate::matmul_tiled()).code.iter().enumerate() { println!("{:3} {:?}", i, ins); } return; }
    if std::env::var("LC_PROF").map(|v| v == "reduce").unwrap_or(false) {
        let n = 300_000usize; let nb = (n + 255) / 256; let kr = crate::block_reduce(); let s = [Sp::B(crate::rnd(n, 5)), Sp::B(vec![0f32; nb]), Sp::I(n as i32)];
        std::env::set_var("LC_THREADS", "1"); run_on(true, &kr, dim(nb, 1, 1), dim(256, 1, 1), &s).0.unwrap(); return; }
    let (m, k, n) = (128usize, 128usize, 128usize); let km = crate::matmul_tiled();
    let s = [Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
    run_on(true, &km, dim(n / 16, m / 16, 1), dim(16, 16, 1), &s).0.unwrap();
}

pub fn run() -> bool {
    let mut ok_all = true; println!("\nSTEP 3: fast lockstep back end");
    // C1: all step 1 launches, bitwise
    let (kv, km, kr) = (crate::vec_add(), crate::matmul_tiled(), crate::block_reduce()); let (mut tot, mut good) = (0, 0);
    for &n in &[1usize, 255, 256, 1000, 100003] { let s = [Sp::B(crate::rnd(n, 1)), Sp::B(crate::rnd(n, 2)), Sp::B(vec![0f32; n]), Sp::I(n as i32)];
        let (ok, note) = same(&kv, dim((n + 255) / 256, 1, 1), dim(256, 1, 1), &s); tot += 1; good += ok as i32; println!("  C1 vec_add n={:<7} bit-identical {} {}", n, ok, note); }
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (64, 64, 64), (100, 50, 70), (33, 129, 17), (128, 128, 128)] {
        let s = [Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
        let (ok, note) = same(&km, dim((n + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), &s); tot += 1; good += ok as i32; println!("  C1 matmul {}x{}x{} bit-identical {} {}", m, k, n, ok, note); }
    for &n in &[1usize, 256, 1000, 12345, 65537] { let nb = (n + 255) / 256; let s = [Sp::B(crate::rnd(n, 5)), Sp::B(vec![0f32; nb]), Sp::I(n as i32)];
        let (ok, note) = same(&kr, dim(nb, 1, 1), dim(256, 1, 1), &s); tot += 1; good += ok as i32; println!("  C1 block_reduce n={:<7} bit-identical {} {}", n, ok, note); }
    let c1 = good == tot; ok_all &= c1; println!("C1 {}/{} launches bit-identical: {}", good, tot, if c1 { "PASS" } else { "FAIL" });
    // C2: negative tests on the fast back end
    let (mut z, ) = (vec![0f32; 8], ); let a1 = [Arg::Buf(Buf { ptr: z.as_mut_ptr(), len: 8 })]; let r1 = crate::fast::launch(&crate::barrier_divergence(), dim(1, 1, 1), dim(4, 1, 1), &a1);
    let a2 = [Arg::Buf(Buf { ptr: z.as_mut_ptr(), len: 8 }), Arg::I32(8)]; let r2 = crate::fast::launch(&crate::out_of_range(), dim(1, 1, 1), dim(1, 1, 1), &a2);
    let c2a = matches!(&r1, Err(e) if e.contains("barrier divergence")); let c2b = matches!(&r2, Err(e) if e.contains("out-of-range"));
    println!("  C2 barrier divergence: {} ({}) | out-of-range: {} ({})", c2a, r1.err().unwrap_or_default(), c2b, r2.err().unwrap_or_default()); ok_all &= c2a && c2b; println!("C2 {}", if c2a && c2b { "PASS" } else { "FAIL" });
    // C3: step 2 suite on the fast back end
    let c3 = crate::step2::run(crate::runtime::Backend::Fast); ok_all &= c3; println!("C3 step 2 suite with the fast back end: {}", if c3 { "PASS" } else { "FAIL" });
    // C4': the C4 measurement repeated 10 times in one process (interpreter once and fast best of 3 each time); passes if the minimum of the ten speed-ups is at least 20x
    let (m, k, n) = (512usize, 512usize, 512usize); let s = [Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)];
    let g = dim(n / 16, m / 16, 1); let b = dim(16, 16, 1); let flop = 2.0 * (m * k * n) as f64;
    { let o = crate::opt::optimise(&km); println!("  optimiser: matmul_tiled registers {} -> {} used; instructions {} -> {}; vec_add {} -> {}; block_reduce {} -> {}", km.regs.len(), crate::opt::used_regs(&o), km.code.len(), o.code.len(), kv.code.len(), crate::opt::optimise(&kv).code.len(), kr.code.len(), crate::opt::optimise(&kr).code.len()); }
    let mut sps = Vec::new(); let mut all_same = true; let mut last = (0.0, 0.0);
    for _ in 0..10 {
        let t = Instant::now(); let (_, oi) = run_on(false, &km, g, b, &s); let ti = t.elapsed().as_secs_f64();
        let mut tf = f64::MAX; let mut of = Vec::new(); for _ in 0..3 { let t = Instant::now(); let (_, o) = run_on(true, &km, g, b, &s); tf = tf.min(t.elapsed().as_secs_f64()); of = o; }
        all_same &= oi[2].iter().zip(&of[2]).all(|(a, b)| a.to_bits() == b.to_bits()); sps.push(ti / tf); last = (ti, tf);
    }
    let mn = sps.iter().cloned().fold(f64::MAX, f64::min); let mx = sps.iter().cloned().fold(0.0, f64::max); let mut sorted = sps.clone(); sorted.sort_by(|a, b| a.partial_cmp(b).unwrap()); let med = (sorted[4] + sorted[5]) / 2.0;
    let c4 = mn >= 20.0 && all_same; ok_all &= c4;
    println!("  C4' ten repetitions of 512^3 matmul, speed-up over the interpreter: {}", sps.iter().map(|x| format!("{:.1}", x)).collect::<Vec<_>>().join(" "));
    println!("  C4' last repetition: interpreter {:.2} s ({:.3} GFLOP/s), fast {:.3} s ({:.3} GFLOP/s); outputs identical in all ten: {}", last.0, flop / last.0 / 1e9, last.1, flop / last.1 / 1e9, all_same);
    println!("C4' minimum {:.1}x, median {:.1}x, maximum {:.1}x (bar: minimum >= 20x): {}", mn, med, mx, if c4 { "PASS" } else { "FAIL" });
    // C5: report only
    let n = 1_000_000usize; let nb = (n + 255) / 256;
    for (name, kk, g, spec) in [("vec_add", &kv, dim(nb, 1, 1), vec![Sp::B(crate::rnd(n, 1)), Sp::B(crate::rnd(n, 2)), Sp::B(vec![0f32; n]), Sp::I(n as i32)]), ("block_reduce", &kr, dim(nb, 1, 1), vec![Sp::B(crate::rnd(n, 5)), Sp::B(vec![0f32; nb]), Sp::I(n as i32)])] {
        let t = Instant::now(); run_on(false, kk, g, dim(256, 1, 1), &spec); let ti = t.elapsed().as_secs_f64();
        let mut tf = f64::MAX; for _ in 0..3 { let t = Instant::now(); run_on(true, kk, g, dim(256, 1, 1), &spec); tf = tf.min(t.elapsed().as_secs_f64()); }
        println!("  C5 {} n=1e6: interpreter {:.3} s, fast {:.4} s ({:.1}x)", name, ti, tf, ti / tf); }
    println!("STEP 3 BARS C1 to C5: {}", if ok_all { "PASS" } else { "FAIL" }); ok_all
}
