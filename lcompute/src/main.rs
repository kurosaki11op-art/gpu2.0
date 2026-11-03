// L Compute step 1: kernels written with the builder, run by the reference interpreter, checked against independent plain references (bars: docs/ROADMAP.md step 1).
mod ir; mod builder; mod interp; mod runtime; mod step2; mod fast; mod step3; mod opt; mod ptx; mod gpusuite; mod step4b;
use builder::B; use interp::*;

fn vec_add() -> ir::Kernel {
    let mut b = B::new("vec_add"); let (a, bb, c) = (b.param_buf(), b.param_buf(), b.param_buf()); let n = b.param_i32();
    let (bi, bd, ti) = (b.bid(0), b.bdim(0), b.tid(0)); let base = b.mul_i(bi, bd); let i = b.add_i(base, ti); let p = b.lt_i(i, n);
    b.if_(p, |b| { let x = b.load_g(a, i); let y = b.load_g(bb, i); let s = b.add_f(x, y); b.store_g(c, i, s); }); b.finish()
}
// C[m,n] = A[m,k] @ B[k,n], 16 x 16 tiles staged through shared memory with barriers
fn matmul_tiled() -> ir::Kernel {
    let mut b = B::new("matmul_tiled"); let (pa, pb, pc) = (b.param_buf(), b.param_buf(), b.param_buf()); let (m, k, n) = (b.param_i32(), b.param_i32(), b.param_i32());
    let (tx, ty) = (b.tid(0), b.tid(1)); let (bx, by) = (b.bid(0), b.bid(1)); let t16 = b.ci(16);
    let r0 = b.mul_i(by, t16); let row = b.add_i(r0, ty); let c0 = b.mul_i(bx, t16); let col = b.add_i(c0, tx);
    let (sa, sb) = (b.shared(256), b.shared(256)); let zf = b.cf(0.0); let acc = b.var_f(zf);
    let sidx0 = b.mul_i(ty, t16); let sidx = b.add_i(sidx0, tx); let c15 = b.ci(15); let kk15 = b.add_i(k, c15); let ntiles = b.div_i(kk15, t16); let z = b.ci(0);
    b.for_range(z, ntiles, 1, |b, t| {
        let t16c = b.ci(16); let toff = b.mul_i(t, t16c);
        let zero = b.cf(0.0); b.store_s(sa, sidx, zero); b.store_s(sb, sidx, zero);
        let acol = b.add_i(toff, tx); let p1 = b.lt_i(row, m); let p2 = b.lt_i(acol, k); let pa_ok = b.and_p(p1, p2);
        b.if_(pa_ok, |b| { let rk = b.mul_i(row, k); let ix = b.add_i(rk, acol); let v = b.load_g(pa, ix); b.store_s(sa, sidx, v); });
        let brow = b.add_i(toff, ty); let q1 = b.lt_i(brow, k); let q2 = b.lt_i(col, n); let pb_ok = b.and_p(q1, q2);
        b.if_(pb_ok, |b| { let rn = b.mul_i(brow, n); let ix = b.add_i(rn, col); let v = b.load_g(pb, ix); b.store_s(sb, sidx, v); });
        b.barrier();
        let z0 = b.ci(0); let c16 = b.ci(16); let tacc = b.var_f(zero); // per-tile partial sum: summing 16 terms first and then adding the tile sum grows the rounding error more slowly than one running sum over all k
        b.for_range(z0, c16, 1, |b, kk| {
            let t16d = b.ci(16); let ai = { let r = b.mul_i(ty, t16d); b.add_i(r, kk) }; let bi = { let r = b.mul_i(kk, t16d); b.add_i(r, tx) };
            let x = b.load_s(sa, ai); let y = b.load_s(sb, bi); let pr = b.mul_f(x, y); let na = b.add_f(tacc, pr); b.mov(tacc, na);
        });
        let nacc = b.add_f(acc, tacc); b.mov(acc, nacc);
        b.barrier();
    });
    let p1 = b.lt_i(row, m); let p2 = b.lt_i(col, n); let pc_ok = b.and_p(p1, p2);
    b.if_(pc_ok, |b| { let rn = b.mul_i(row, n); let ix = b.add_i(rn, col); b.store_g(pc, ix, acc); }); b.finish()
}
// C[m,n] = A[m,k] @ B[k,n], register blocked: a 64 x 64 block tile, 16 x 16 threads, each thread computes 4 x 4 outputs (rows ty*4+i, columns tx+16*j), k tile 16.
// Same summation order as matmul_tiled (16 products summed first, then added to the running total), so the bits are the same.
fn matmul_reg() -> ir::Kernel { matmul_reg_impl("matmul_reg", false) }
// the same kernel with a fused multiply-add in the inner loop (its own bits: one rounding per multiply-add)
fn matmul_fma() -> ir::Kernel { matmul_reg_impl("matmul_fma", true) }
fn matmul_reg_impl(name: &str, fma: bool) -> ir::Kernel {
    let mut b = B::new(name); let (pa, pb, pc) = (b.param_buf(), b.param_buf(), b.param_buf()); let (m, k, n) = (b.param_i32(), b.param_i32(), b.param_i32());
    let (tx, ty) = (b.tid(0), b.tid(1)); let (bx, by) = (b.bid(0), b.bid(1)); let (c16, c64, c256) = (b.ci(16), b.ci(64), b.ci(256)); let c15 = b.ci(15);
    let (sa, sb) = (b.shared(1024), b.shared(1024)); let zero = b.cf(0.0);
    let t = { let r = b.mul_i(ty, c16); b.add_i(r, tx) }; let row0 = b.mul_i(by, c64); let col0 = b.mul_i(bx, c64);
    let acc: Vec<ir::Reg> = (0..16).map(|_| b.var_f(zero)).collect();
    let kk15 = b.add_i(k, c15); let ntiles = b.div_i(kk15, c16); let z = b.ci(0);
    let ty64 = b.mul_i(ty, c64); // ty * 4 rows * 16 floats = row base of this thread's A rows in shared memory
    b.for_range(z, ntiles, 1, |b, tile| {
        let c16b = b.ci(16); let toff = b.mul_i(tile, c16b);
        for j in 0..4 {
            let cj = b.ci(j * 256); let e = b.add_i(t, cj);
            // A tile: 64 rows x 16 columns, element e = row * 16 + column
            let (c16a, c64a) = (b.ci(16), b.ci(64)); let ar = b.div_i(e, c16a); let ac = b.rem_i(e, c16a); let grow = b.add_i(row0, ar); let gcol = b.add_i(toff, ac);
            let p1 = b.lt_i(grow, m); let p2 = b.lt_i(gcol, k); let pa_ok = b.and_p(p1, p2); let z0 = b.cf(0.0); let va = b.var_f(z0);
            b.if_(pa_ok, |b| { let rk = b.mul_i(grow, k); let ix = b.add_i(rk, gcol); let v = b.load_g(pa, ix); b.mov(va, v); }); b.store_s(sa, e, va);
            // B tile: 16 rows x 64 columns, element e = row * 64 + column
            let br = b.div_i(e, c64a); let bc = b.rem_i(e, c64a); let grow2 = b.add_i(toff, br); let gcol2 = b.add_i(col0, bc);
            let q1 = b.lt_i(grow2, k); let q2 = b.lt_i(gcol2, n); let pb_ok = b.and_p(q1, q2); let vb = b.var_f(z0);
            b.if_(pb_ok, |b| { let rn = b.mul_i(grow2, n); let ix = b.add_i(rn, gcol2); let v = b.load_g(pb, ix); b.mov(vb, v); }); b.store_s(sb, e, vb);
        }
        b.barrier();
        let tacc: Vec<ir::Reg> = (0..16).map(|_| b.var_f(zero)).collect(); let z1 = b.ci(0); let c16c = b.ci(16);
        b.for_range(z1, c16c, 1, |b, kk| {
            let c16d = b.ci(16); let c64d = b.ci(64);
            let av: Vec<ir::Reg> = (0..4).map(|i| { let off = b.ci(i * 16); let r = b.add_i(ty64, off); let ix = b.add_i(r, kk); b.load_s(sa, ix) }).collect();
            let kb = { let r = b.mul_i(kk, c64d); b.add_i(r, tx) };
            let bv: Vec<ir::Reg> = (0..4).map(|j| { let off = b.ci(j * 16); let ix = b.add_i(kb, off); b.load_s(sb, ix) }).collect();
            let _ = c16d;
            for i in 0..4 { for j in 0..4 { let na = if fma { b.fma_f(av[i], bv[j], tacc[i * 4 + j]) } else { let pr = b.mul_f(av[i], bv[j]); b.add_f(tacc[i * 4 + j], pr) }; b.mov(tacc[i * 4 + j], na); } }
        });
        for q in 0..16 { let na = b.add_f(acc[q], tacc[q]); b.mov(acc[q], na); }
        b.barrier();
    });
    for i in 0..4 { for j in 0..4 {
        let ci_ = b.ci(i as i32 * 0); let _ = ci_; let four = b.ci(4); let ty4 = b.mul_i(ty, four); let io = b.ci(i as i32); let r1 = b.add_i(ty4, io); let row = b.add_i(row0, r1);
        let jo = b.ci(j as i32 * 16); let c1 = b.add_i(tx, jo); let col = b.add_i(col0, c1);
        let p1 = b.lt_i(row, m); let p2 = b.lt_i(col, n); let ok = b.and_p(p1, p2); let a = acc[(i * 4 + j) as usize];
        b.if_(ok, |b| { let rn = b.mul_i(row, n); let ix = b.add_i(rn, col); b.store_g(pc, ix, a); });
    } } b.finish()
}
// Second-generation matmul (step 4c): thread tile tm x tm (4 or 8) with 16 x 16 threads, block tile (16*tm) x (16*tm), k tile 16, fused multiply-add, one running sum per output over all k (its own bits).
// The index arithmetic that does not depend on the k tile (which element of the tile this thread loads, its row/column predicates) is computed once before the tile loop.
fn matmul_fma4() -> ir::Kernel { matmul_v2("matmul_fma4", 4) }
fn matmul_fma8() -> ir::Kernel { matmul_v2("matmul_fma8", 8) }
fn matmul_v2(name: &str, tm: i32) -> ir::Kernel {
    let bt = 16 * tm; let nl = tm; // elements of each tile loaded per thread: bt * 16 / 256 = tm
    let mut b = B::new(name); let (pa, pb, pc) = (b.param_buf(), b.param_buf(), b.param_buf()); let (m, k, n) = (b.param_i32(), b.param_i32(), b.param_i32());
    let (tx, ty) = (b.tid(0), b.tid(1)); let (bx, by) = (b.bid(0), b.bid(1)); let (c16, cbt, c15) = (b.ci(16), b.ci(bt), b.ci(15));
    let (sa, sb) = (b.shared((bt * 16) as usize), b.shared((16 * bt) as usize)); let zero = b.cf(0.0);
    let t = { let r = b.mul_i(ty, c16); b.add_i(r, tx) }; let row0 = b.mul_i(by, cbt); let col0 = b.mul_i(bx, cbt);
    let (mut a_e, mut a_ac, mut a_rowk, mut a_rowok, mut b_e, mut b_br, mut b_col, mut b_colok) = (vec![], vec![], vec![], vec![], vec![], vec![], vec![], vec![]);
    for j in 0..nl {
        let cj = b.ci(j * 256); let e = b.add_i(t, cj);
        let ar = b.div_i(e, c16); let ac = b.rem_i(e, c16); let grow = b.add_i(row0, ar); let rowk = b.mul_i(grow, k); let rowok = b.lt_i(grow, m); a_e.push(e); a_ac.push(ac); a_rowk.push(rowk); a_rowok.push(rowok);
        let br = b.div_i(e, cbt); let bc = b.rem_i(e, cbt); let bcol = b.add_i(col0, bc); let colok = b.lt_i(bcol, n); b_e.push(e); b_br.push(br); b_col.push(bcol); b_colok.push(colok);
    }
    let acc: Vec<ir::Reg> = (0..tm * tm).map(|_| b.var_f(zero)).collect();
    let kk15 = b.add_i(k, c15); let ntiles = b.div_i(kk15, c16); let z = b.ci(0); let ctm16 = b.ci(tm * 16); let ty_base = b.mul_i(ty, ctm16);
    b.for_range(z, ntiles, 1, |b, tile| {
        let c16b = b.ci(16); let toff = b.mul_i(tile, c16b);
        for j in 0..nl as usize {
            let gcol = b.add_i(toff, a_ac[j]); let p2 = b.lt_i(gcol, k); let ok = b.and_p(a_rowok[j], p2); let z0 = b.cf(0.0); let va = b.var_f(z0);
            b.if_(ok, |b| { let ix = b.add_i(a_rowk[j], gcol); let v = b.load_g(pa, ix); b.mov(va, v); }); b.store_s(sa, a_e[j], va);
            let grow2 = b.add_i(toff, b_br[j]); let q1 = b.lt_i(grow2, k); let ok2 = b.and_p(q1, b_colok[j]); let vb = b.var_f(z0);
            b.if_(ok2, |b| { let rn = b.mul_i(grow2, n); let ix = b.add_i(rn, b_col[j]); let v = b.load_g(pb, ix); b.mov(vb, v); }); b.store_s(sb, b_e[j], vb);
        }
        b.barrier();
        let z1 = b.ci(0); let c16c = b.ci(16);
        b.for_range(z1, c16c, 1, |b, kk| {
            let cbt2 = b.ci(bt);
            let av: Vec<ir::Reg> = (0..tm).map(|i| { let off = b.ci(i * 16); let r = b.add_i(ty_base, off); let ix = b.add_i(r, kk); b.load_s(sa, ix) }).collect();
            let kb = { let r = b.mul_i(kk, cbt2); b.add_i(r, tx) };
            let bv: Vec<ir::Reg> = (0..tm).map(|j| { let off = b.ci(j * 16); let ix = b.add_i(kb, off); b.load_s(sb, ix) }).collect();
            for i in 0..tm as usize { for j in 0..tm as usize { let na = b.fma_f(av[i], bv[j], acc[i * tm as usize + j]); b.mov(acc[i * tm as usize + j], na); } }
        });
        b.barrier();
    });
    for i in 0..tm { for j in 0..tm {
        let ctm = b.ci(tm); let ty4 = b.mul_i(ty, ctm); let io = b.ci(i); let r1 = b.add_i(ty4, io); let row = b.add_i(row0, r1);
        let jo = b.ci(j * 16); let c1 = b.add_i(tx, jo); let col = b.add_i(col0, c1);
        let p1 = b.lt_i(row, m); let p2 = b.lt_i(col, n); let ok = b.and_p(p1, p2); let a = acc[(i * tm + j) as usize];
        b.if_(ok, |b| { let rn = b.mul_i(row, n); let ix = b.add_i(rn, col); b.store_g(pc, ix, a); });
    } } b.finish()
}
// per-block sum of 256 elements with a shared-memory tree reduction
fn block_reduce() -> ir::Kernel {
    let mut b = B::new("block_reduce"); let (px, po) = (b.param_buf(), b.param_buf()); let n = b.param_i32(); let sd = b.shared(256);
    let tid = b.tid(0); let bid = b.bid(0); let c256 = b.ci(256); let base = b.mul_i(bid, c256); let i = b.add_i(base, tid);
    let zero = b.cf(0.0); b.store_s(sd, tid, zero); let p = b.lt_i(i, n); b.if_(p, |b| { let v = b.load_g(px, i); b.store_s(sd, tid, v); }); b.barrier();
    let c128 = b.ci(128); let s = b.var_i(c128); let one = b.ci(1); let z = b.ci(0);
    b.while_(|b| b.gt_i(s, z), |b| {
        let act = b.lt_i(tid, s); b.if_(act, |b| { let x = b.load_s(sd, tid); let j = b.add_i(tid, s); let y = b.load_s(sd, j); let r = b.add_f(x, y); b.store_s(sd, tid, r); });
        b.barrier(); let ns = b.shr_i(s, one); b.mov(s, ns);
    });
    let first = b.lt_i(tid, one); b.if_(first, |b| { let r = b.load_s(sd, z); b.store_g(po, bid, r); }); b.finish()
}
// two kernels that must be rejected
fn barrier_divergence() -> ir::Kernel { let mut b = B::new("barrier_divergence"); let _x = b.param_buf(); let tid = b.tid(0); let one = b.ci(1); let p = b.lt_i(tid, one); let _s = b.shared(4); b.if_(p, |b| b.ret()); b.barrier(); b.finish() }
fn out_of_range() -> ir::Kernel { let mut b = B::new("out_of_range"); let x = b.param_buf(); let n = b.param_i32(); let _v = b.load_g(x, n); b.finish() }

fn host(v: &mut Vec<f32>) -> Arg { Arg::Buf(Buf { ptr: v.as_mut_ptr(), len: v.len() }) }
fn rnd(n: usize, seed: u64) -> Vec<f32> { let mut s = seed; (0..n).map(|_| { s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407); ((s >> 40) as f32 / 16777216.0) * 2.0 - 1.0 }).collect() }
fn relerr(got: f32, want: f64) -> f64 { (got as f64 - want).abs() / want.abs().max(1.0) }

fn main() {
    { let a: Vec<String> = std::env::args().collect(); if a.len() == 3 && a[1] == "--emit-gpu" { gpusuite::export(&a[2]); return; } }
    if std::env::var("LC_PROF").is_ok() { step3::prof(); return; } // profiling entry: fast back end only
    let mut all_ok = true; let mut worst = 0f64; let mut ok_1b = true; // ok_1b: the step 1b rule of docs/ROADMAP.md (exact agreement with the sequential fp32 sum, and within k x 6e-8 x sum of |terms| of a float64 reference)
    let kv = vec_add();
    for &n in &[1usize, 255, 256, 1000, 100003] {
        let (mut a, mut bb, mut c) = (rnd(n, 1), rnd(n, 2), vec![0f32; n]); let args = [host(&mut a), host(&mut bb), host(&mut c), Arg::I32(n as i32)];
        launch(&kv, dim((n + 255) / 256, 1, 1), dim(256, 1, 1), &args).unwrap();
        let e = (0..n).map(|i| relerr(c[i], a[i] as f64 + bb[i] as f64)).fold(0f64, f64::max); worst = worst.max(e); let ok = e <= 1e-5; all_ok &= ok;
        println!("vec_add       n={:<7} max relative error {:.1e}  {}", n, e, if ok { "ok" } else { "FAIL" });
    }
    let km = matmul_tiled();
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (64, 64, 64), (100, 50, 70), (33, 129, 17), (128, 128, 128)] {
        let (mut a, mut bb, mut c) = (rnd(m * k, 3), rnd(k * n, 4), vec![0f32; m * n]); let args = [host(&mut a), host(&mut bb), host(&mut c), Arg::I32(m as i32), Arg::I32(k as i32), Arg::I32(n as i32)];
        launch(&km, dim((n + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), &args).unwrap();
        let mut e = 0f64; for i in 0..m { for j in 0..n { let mut s = 0f64; for kk in 0..k { s += a[i * k + kk] as f64 * bb[kk * n + j] as f64; } e = e.max(relerr(c[i * n + j], s)); } }
        let mut e32 = 0f32; for i in 0..m { for j in 0..n { let mut s = 0f32; let mut t0 = 0; while t0 < k { let mut tp = 0f32; for kk in t0..(t0 + 16).min(k) { tp += a[i * k + kk] * bb[kk * n + j]; } s += tp; t0 += 16; } e32 = e32.max((c[i * n + j] - s).abs()); } }
        let mut ratio = 0f64; for i in 0..m { for j in 0..n { let (mut s, mut sa) = (0f64, 0f64); for kk in 0..k { let t = a[i * k + kk] as f64 * bb[kk * n + j] as f64; s += t; sa += t.abs(); } ratio = ratio.max((c[i * n + j] as f64 - s).abs() / (k as f64 * 6e-8 * sa).max(1e-30)); } }
        let b1 = e32 == 0.0 && ratio <= 1.0; ok_1b &= b1;
        worst = worst.max(e); let ok = e <= 1e-5; all_ok &= ok; println!("matmul_tiled  {}x{}x{}: max relative error {:.2e}  {}   | step 1b: exact vs sequential fp32 {}, error is {:.3} of the rounding bound  {}", m, k, n, e, if ok { "ok" } else { "FAIL" }, if e32 == 0.0 { "yes" } else { "NO" }, ratio, if b1 { "ok" } else { "FAIL" });
    }
    let kr = block_reduce();
    for &n in &[1usize, 256, 1000, 12345, 65537] {
        let nb = (n + 255) / 256; let (mut x, mut o) = (rnd(n, 5), vec![0f32; nb]); let args = [host(&mut x), host(&mut o), Arg::I32(n as i32)];
        launch(&kr, dim(nb, 1, 1), dim(256, 1, 1), &args).unwrap();
        let mut e = 0f64; for blk in 0..nb { let s: f64 = (blk * 256..((blk + 1) * 256).min(n)).map(|i| x[i] as f64).sum(); e = e.max(relerr(o[blk], s)); }
        worst = worst.max(e); let ok = e <= 1e-5; all_ok &= ok; println!("block_reduce  n={:<7} max relative error {:.1e}  {}", n, e, if ok { "ok" } else { "FAIL" });
    }
    // negative tests: the interpreter must report these
    let mut z = vec![0f32; 8]; let args = [host(&mut z)]; let r = launch(&barrier_divergence(), dim(1, 1, 1), dim(4, 1, 1), &args);
    let ok = matches!(&r, Err(e) if e.contains("barrier divergence")); all_ok &= ok; println!("negative test barrier divergence: {}  ({})", if ok { "detected" } else { "NOT DETECTED" }, r.err().unwrap_or_default());
    let args = [host(&mut z), Arg::I32(8)]; let r = launch(&out_of_range(), dim(1, 1, 1), dim(1, 1, 1), &args);
    let ok = matches!(&r, Err(e) if e.contains("out-of-range")); all_ok &= ok; println!("negative test out-of-range load: {}  ({})", if ok { "detected" } else { "NOT DETECTED" }, r.err().unwrap_or_default());
    println!("\nSTEP 1 BAR as first written (each kernel on at least 5 shapes within 1e-5, two negative tests detected): worst relative error {:.1e}, {}", worst, if all_ok { "PASS" } else { "FAIL" });
    println!("STEP 1b RULE for matrix products (written after the step 1 run; a re-specification, not a pass of the first bar): {}", if ok_1b { "all shapes meet it" } else { "NOT MET" });
    step2::run(runtime::Backend::Interp);
    step3::run();
    step4b::run();
}
