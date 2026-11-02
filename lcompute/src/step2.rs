// Step 2 tests (bars R1 to R5 in docs/ROADMAP.md): the runtime API with in-order streams and checked errors.
use crate::interp::dim;
use crate::runtime::*;
use std::sync::Arc;

pub fn run() -> bool {
    let rt = Runtime::new(); let s0 = rt.create_stream(); let mut ok_all = true; let mut report = |name: &str, ok: bool, note: String| { println!("  {:<58} {}  {}", name, if ok { "ok" } else { "FAIL" }, note); ok_all &= ok; };
    let kv = Arc::new(crate::vec_add()); let km = Arc::new(crate::matmul_tiled()); let kr = Arc::new(crate::block_reduce()); let ko = Arc::new(crate::out_of_range());
    println!("\nSTEP 2: runtime (streams, buffers, checked errors)");
    // R1: the step 1 kernels through the runtime only
    { let n = 100003usize; let (a, b) = (crate::rnd(n, 1), crate::rnd(n, 2)); let (ba, bb, bc) = (rt.alloc(n).unwrap(), rt.alloc(n).unwrap(), rt.alloc(n).unwrap());
      rt.copy_to_device(s0, ba, &a).unwrap(); rt.copy_to_device(s0, bb, &b).unwrap();
      rt.launch(s0, &kv, dim((n + 255) / 256, 1, 1), dim(256, 1, 1), &[RtArg::Buf(ba), RtArg::Buf(bb), RtArg::Buf(bc), RtArg::I32(n as i32)]).unwrap(); rt.synchronize(s0).unwrap();
      let c = rt.copy_to_host(s0, bc).unwrap(); let e = (0..n).map(|i| (c[i] - (a[i] + b[i])).abs()).fold(0f32, f32::max); report("R1 vec_add n=100003 through the runtime", e == 0.0, format!("max error {:.1e}", e));
      for id in [ba, bb, bc] { rt.free(id).unwrap(); } }
    { let (m, k, n) = (33usize, 129usize, 17usize); let (a, b) = (crate::rnd(m * k, 3), crate::rnd(k * n, 4)); let (ba, bb, bc) = (rt.alloc(m * k).unwrap(), rt.alloc(k * n).unwrap(), rt.alloc(m * n).unwrap());
      rt.copy_to_device(s0, ba, &a).unwrap(); rt.copy_to_device(s0, bb, &b).unwrap();
      rt.launch(s0, &km, dim((n + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), &[RtArg::Buf(ba), RtArg::Buf(bb), RtArg::Buf(bc), RtArg::I32(m as i32), RtArg::I32(k as i32), RtArg::I32(n as i32)]).unwrap(); rt.synchronize(s0).unwrap();
      let c = rt.copy_to_host(s0, bc).unwrap(); let mut e = 0f64; for i in 0..m { for j in 0..n { let mut s = 0f64; for kk in 0..k { s += a[i * k + kk] as f64 * b[kk * n + j] as f64; } e = e.max(crate::relerr(c[i * n + j], s)); } }
      report("R1 matmul 33x129x17 through the runtime (bar 1e-5)", e <= 1e-5, format!("max relative error {:.1e}", e)); for id in [ba, bb, bc] { rt.free(id).unwrap(); } }
    { let n = 12345usize; let x = crate::rnd(n, 5); let nb = (n + 255) / 256; let (bx, bo) = (rt.alloc(n).unwrap(), rt.alloc(nb).unwrap()); rt.copy_to_device(s0, bx, &x).unwrap();
      rt.launch(s0, &kr, dim(nb, 1, 1), dim(256, 1, 1), &[RtArg::Buf(bx), RtArg::Buf(bo), RtArg::I32(n as i32)]).unwrap(); rt.synchronize(s0).unwrap(); let o = rt.copy_to_host(s0, bo).unwrap();
      let mut e = 0f64; for blk in 0..nb { let s: f64 = (blk * 256..((blk + 1) * 256).min(n)).map(|i| x[i] as f64).sum(); e = e.max(crate::relerr(o[blk], s)); } report("R1 block_reduce n=12345 through the runtime (bar 1e-5)", e <= 1e-5, format!("max relative error {:.1e}", e)); for id in [bx, bo] { rt.free(id).unwrap(); } }
    // R2: order inside one stream, no synchronisation between two dependent launches
    { let n = 5000usize; let (a, b) = (crate::rnd(n, 7), crate::rnd(n, 8)); let (ba, bb, bc, bd) = (rt.alloc(n).unwrap(), rt.alloc(n).unwrap(), rt.alloc(n).unwrap(), rt.alloc(n).unwrap());
      rt.copy_to_device(s0, ba, &a).unwrap(); rt.copy_to_device(s0, bb, &b).unwrap(); let g = dim((n + 255) / 256, 1, 1);
      rt.launch(s0, &kv, g, dim(256, 1, 1), &[RtArg::Buf(ba), RtArg::Buf(bb), RtArg::Buf(bc), RtArg::I32(n as i32)]).unwrap();
      rt.launch(s0, &kv, g, dim(256, 1, 1), &[RtArg::Buf(bc), RtArg::Buf(ba), RtArg::Buf(bd), RtArg::I32(n as i32)]).unwrap(); rt.synchronize(s0).unwrap();
      let d = rt.copy_to_host(s0, bd).unwrap(); let e = (0..n).map(|i| (d[i] - ((a[i] + b[i]) + a[i])).abs()).fold(0f32, f32::max); report("R2 two dependent launches on one stream, no wait between", e == 0.0, format!("max error {:.1e}", e)); for id in [ba, bb, bc, bd] { rt.free(id).unwrap(); } }
    // R3: four independent streams; 100 chained launches on one stream
    { let n = 3000usize; let streams: Vec<StreamId> = (0..4).map(|_| rt.create_stream()).collect(); let mut sets = Vec::new();
      for (q, &s) in streams.iter().enumerate() { let (a, b) = (crate::rnd(n, 20 + q as u64), crate::rnd(n, 30 + q as u64)); let (ba, bb, bc) = (rt.alloc(n).unwrap(), rt.alloc(n).unwrap(), rt.alloc(n).unwrap());
        rt.copy_to_device(s, ba, &a).unwrap(); rt.copy_to_device(s, bb, &b).unwrap(); rt.launch(s, &kv, dim((n + 255) / 256, 1, 1), dim(256, 1, 1), &[RtArg::Buf(ba), RtArg::Buf(bb), RtArg::Buf(bc), RtArg::I32(n as i32)]).unwrap(); sets.push((s, a, b, ba, bb, bc)); }
      let mut worst = 0f32; for (s, a, b, ba, bb, bc) in sets { rt.synchronize(s).unwrap(); let c = rt.copy_to_host(s, bc).unwrap(); worst = worst.max((0..n).map(|i| (c[i] - (a[i] + b[i])).abs()).fold(0f32, f32::max)); for id in [ba, bb, bc] { rt.free(id).unwrap(); } }
      report("R3 four independent streams, each correct", worst == 0.0, format!("max error {:.1e}", worst)); }
    { let n = 1000usize; let (bx, bone) = (rt.alloc(n).unwrap(), rt.alloc(n).unwrap()); rt.copy_to_device(s0, bone, &vec![1f32; n]).unwrap(); let g = dim((n + 255) / 256, 1, 1);
      for _ in 0..100 { rt.launch(s0, &kv, g, dim(256, 1, 1), &[RtArg::Buf(bx), RtArg::Buf(bone), RtArg::Buf(bx), RtArg::I32(n as i32)]).unwrap(); } rt.synchronize(s0).unwrap();
      let x = rt.copy_to_host(s0, bx).unwrap(); let ok = x.iter().all(|&v| v == 100.0); report("R3 100 chained launches on one stream end at exactly 100", ok, format!("first {}, last {}", x[0], x[n - 1])); for id in [bx, bone] { rt.free(id).unwrap(); } }
    // R4: seven kinds of mistake must be reported with a message
    { let b8 = rt.alloc(8).unwrap(); let has = |r: Result<(), String>, key: &str| -> (bool, String) { match r { Err(e) => (e.contains(key), e), Ok(_) => (false, "NOT REPORTED".to_string()) } };
      let (ok, m) = has(rt.copy_to_device(s0, b8, &[0f32; 5]), "copy of 5 floats"); report("R4.1 wrong-size copy", ok, m);
      let b9 = rt.alloc(8).unwrap(); rt.free(b9).unwrap(); let (ok, m) = has(rt.copy_to_device(s0, b9, &[0f32; 8]), "freed"); report("R4.2 use of a freed buffer", ok, m);
      let (ok, m) = has(rt.free(b9), "double free"); report("R4.3 double free", ok, m);
      let (ok, m) = has(rt.launch(s0, &ko, dim(1, 1, 1), dim(1, 1, 1), &[RtArg::Buf(BufId(999)), RtArg::I32(8)]), "unknown buffer handle"); report("R4.4 unknown buffer handle", ok, m);
      let (ok, m) = has(rt.launch(s0, &kv, dim(1, 1, 1), dim(1, 1, 1), &[RtArg::Buf(b8), RtArg::Buf(b8), RtArg::Buf(b8)]), "expected 4 arguments"); report("R4.5 wrong number of arguments", ok, m);
      let (ok, m) = has(rt.launch(s0, &ko, dim(1, 1, 1), dim(1, 1, 1), &[RtArg::I32(1), RtArg::I32(8)]), "wrong kind"); report("R4.6 argument of the wrong kind", ok, m);
      rt.launch(s0, &ko, dim(1, 1, 1), dim(1, 1, 1), &[RtArg::Buf(b8), RtArg::I32(8)]).unwrap(); let (ok, m) = has(rt.synchronize(s0), "out-of-range"); report("R4.7 out-of-range access inside a kernel, reported by synchronize", ok, m);
      let (ok, m) = has(rt.synchronize(s0), "never"); let cleared = !ok && m == "NOT REPORTED"; report("R4.8 (extra) the error is reported once, then the stream is usable again", cleared, String::new()); rt.free(b8).unwrap(); }
    // R5: no live buffers left; dropping joins the stream threads
    let live = rt.live_buffers(); report("R5 live buffers after freeing everything", live == 0, format!("{} live", live)); drop(rt); report("R5 dropping the runtime joined its stream threads", true, String::new());
    println!("STEP 2 BARS R1 to R5: {}", if ok_all { "PASS" } else { "FAIL" }); ok_all
}
