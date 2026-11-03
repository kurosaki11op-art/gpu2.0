// Step 4d tests (bar Q8a and Q8b in docs/ROADMAP.md): coverage and soundness of the range analysis, and the launch-bounds rules.
use crate::builder::B;
use crate::interp::{self, dim, Arg, Buf};
use crate::ir::Kernel;
use crate::runtime::*;
use std::sync::Arc;

struct Rng(u64);
impl Rng { fn next(&mut self) -> u64 { self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407); self.0 >> 33 } fn below(&mut self, n: u64) -> u64 { self.next() % n } }

// random index expression over thread ids, small constants, and (optionally) a loop variable
fn expr(b: &mut B, r: &mut Rng, depth: u32, leaves: &Vec<crate::ir::Reg>) -> crate::ir::Reg {
    if depth == 0 || r.below(4) == 0 { return if r.below(3) == 0 { b.ci(r.below(40) as i32 - 5) } else { leaves[r.below(leaves.len() as u64) as usize] }; }
    let x = expr(b, r, depth - 1, leaves);
    let y = if r.below(2) == 0 { b.ci(r.below(20) as i32 + 1) } else { expr(b, r, depth - 1, leaves) };
    let sh = b.ci(r.below(5) as i32); let m = b.ci((1u64 << r.below(9)) as i32 - 1); let d = b.ci(r.below(15) as i32 + 1);
    match r.below(11) { 0 => b.add_i(x, y), 1 => b.sub_i(x, y), 2 => b.mul_i(x, y), 3 => b.div_i(x, d), 4 => b.rem_i(x, d), 5 => b.shr_i(x, sh), 6 => b.shl_i(x, sh), 7 => b.min_i(x, y), 8 => b.max_i(x, y), 9 => b.and_i(x, m), _ => b.add_i(x, d) }
}

pub fn run() -> bool {
    println!("\nSTEP 4d: range analysis (proving shared-memory accesses in range)");
    let mut all = true;
    // Q8a coverage on the matmul kernels
    for (kk, name) in [(crate::matmul_fma8db(), "matmul_fma8db"), (crate::matmul_fma8x4(), "matmul_fma8x4"), (crate::matmul_fma8x4db(), "matmul_fma8x4db")] {
        let (p1, t1) = crate::range::coverage(&kk); let u = crate::opt::optimise_with(&kk, 40000); let (p2, t2) = crate::range::coverage(&u);
        let ok = p1 * 100 >= 95 * t1 && p2 * 100 >= 95 * t2; all &= ok;
        println!("  Q8a {:<16} shared accesses proved safe: as written {}/{}, after unrolling {}/{}  {}", name, p1, t1, p2, t2, if ok { "ok" } else { "FAIL" });
    }
    // Q8b soundness: random expressions (straight line, and inside a loop with a constant trip count), proved => the interpreter must not report an out-of-range shared access
    let (mut trials, mut proved, mut oob, mut violations, mut proved_oob_free) = (0u32, 0u32, 0u32, 0u32, 0u32); let mut r = Rng(12345);
    let shapes = [(1usize, 1usize), (4, 1), (16, 1), (5, 3), (16, 16), (7, 2), (32, 1), (3, 5)]; let sizes = [1usize, 4, 16, 17, 50, 256, 1000, 5000];
    for t in 0..20000u32 {
        let (bx, by) = shapes[r.below(shapes.len() as u64) as usize]; let len = sizes[r.below(sizes.len() as u64) as usize]; let in_loop = t % 3 == 0; let nested = t % 3 == 1;
        let mut b = B::new("fuzz"); if r.below(8) != 0 { b.launch_bounds(bx, by, 1); } let sh = b.shared(len); let (tx, ty) = (b.tid(0), b.tid(1)); let mut leaves = vec![tx, ty]; leaves.push(b.bdim(0));
        if in_loop { let (z, n) = (b.ci(r.below(3) as i32), b.ci(r.below(20) as i32 + 1)); let step = r.below(3) as i32 + 1; b.for_range(z, n, step, |b, i| { let mut l = leaves.clone(); l.push(i); let ix = expr(b, &mut r, 3, &l); let _v = b.load_s(sh, ix); }); }
        else if nested { let (z, n) = (b.ci(0), b.ci(r.below(6) as i32 + 1)); let (z2, n2) = (b.ci(r.below(3) as i32), b.ci(r.below(9) as i32 + 1)); let st2 = r.below(2) as i32 + 1;
            b.for_range(z, n, 1, |b, i| { b.for_range(z2, n2, st2, |b, j| { let mut l = leaves.clone(); l.push(i); l.push(j); let ix = expr(b, &mut r, 3, &l); let _v = b.load_s(sh, ix); }); }); }
        else { let ix = expr(&mut b, &mut r, 3, &leaves); let _v = b.load_s(sh, ix); }
        let k = b.finish(); let safe = crate::range::safe_shared(&k); let pos = k.code.iter().position(|i| matches!(i, crate::ir::Inst::LdS(..))).unwrap(); let is_proved = safe[pos];
        let launch = k.bounds.map(|b| (b[0], b[1])).unwrap_or((bx, by)); let res = interp::launch(&k, dim(1, 1, 1), dim(launch.0, launch.1, 1), &[]);
        let is_oob = matches!(&res, Err(e) if e.contains("out-of-range shared")); trials += 1; if is_proved { proved += 1; if !is_oob { proved_oob_free += 1; } } if is_oob { oob += 1; } if is_proved && is_oob { violations += 1; if violations <= 3 { println!("  VIOLATION: proved safe but out of range: {:?}", k.code); } }
        // kernels without declared bounds are launched with a shape the analysis cannot know: only count kernels with bounds as violations when launched in shape (always true here)
    }
    let q8b = violations == 0 && proved >= 4000 && oob >= 2000; all &= q8b;
    println!("  Q8b fuzz: {} random kernels; proved safe {}; reported out of range by the interpreter {}; **proved but out of range: {}**  {}", trials, proved, oob, violations, if q8b { "ok" } else { "FAIL" });
    // negative kernels
    let ks = crate::shared_oob(); let safe = crate::range::safe_shared(&ks); let pos = ks.code.iter().position(|i| matches!(i, crate::ir::Inst::LdS(..))).unwrap();
    let mut x = vec![0f32; 16]; let args = [Arg::Buf(Buf { ptr: x.as_mut_ptr(), len: 16 })]; let res = interp::launch(&ks, dim(1, 1, 1), dim(16, 1, 1), &args);
    let ok = !safe[pos] && matches!(&res, Err(e) if e.contains("out-of-range shared")); all &= ok; println!("  Q8b negative kernel (index = thread id + 1 on an array as long as the block): proved safe {}, interpreter {}  {}", safe[pos], if res.is_err() { "reports it" } else { "does NOT report it" }, if ok { "ok" } else { "FAIL" });
    // launch bounds: a wrong block shape is rejected by the interpreter, the fast back end and the runtime
    let km = Arc::new(crate::matmul_fma8db()); let mut a = vec![0f32; 128 * 128]; let args = [Arg::Buf(Buf { ptr: a.as_mut_ptr(), len: a.len() }), Arg::Buf(Buf { ptr: a.as_mut_ptr(), len: a.len() }), Arg::Buf(Buf { ptr: a.as_mut_ptr(), len: a.len() }), Arg::I32(128), Arg::I32(128), Arg::I32(128)];
    let r1 = interp::launch(&km, dim(1, 1, 1), dim(8, 8, 1), &args); let r2 = crate::fast::launch(&km, dim(1, 1, 1), dim(8, 8, 1), &args);
    let rt = Runtime::new(); let s0 = rt.create_stream(); let bb = rt.alloc(128 * 128).unwrap(); let r3 = rt.launch(s0, &km, dim(1, 1, 1), dim(8, 8, 1), &[RtArg::Buf(bb), RtArg::Buf(bb), RtArg::Buf(bb), RtArg::I32(128), RtArg::I32(128), RtArg::I32(128)]);
    let ok = [&r1, &r2, &r3].iter().all(|r| matches!(r, Err(e) if e.contains("launch bounds"))); all &= ok;
    println!("  Q8b wrong block shape (8 x 8 for a kernel declaring 16 x 16): interpreter {}, fast back end {}, runtime {}  {}", if r1.is_err() { "rejects" } else { "ACCEPTS" }, if r2.is_err() { "rejects" } else { "ACCEPTS" }, if r3.is_err() { "rejects" } else { "ACCEPTS" }, if ok { "ok" } else { "FAIL" });
    println!("STEP 4d BARS Q8a and Q8b (CPU part): {}", if all { "PASS" } else { "FAIL" }); let _: Option<Kernel> = None; all
}
