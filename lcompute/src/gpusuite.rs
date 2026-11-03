// Exports the step 4 GPU suite: PTX for every kernel and, for every launch of the step 1 suite, the inputs and the interpreter's outputs as raw little-endian f32 files, so a GPU runner (tools/gpu_runner.py) can check the GPU result bit for bit.
// Usage: lcompute --emit-gpu DIR
use crate::interp::dim;
use crate::ir::Kernel;
use crate::step3::{run_on, Sp};
use std::fs;

fn bytes(v: &[f32]) -> Vec<u8> { v.iter().flat_map(|x| x.to_le_bytes()).collect() }

fn case(dir: &str, name: &str, k: &Kernel, grid: crate::interp::Dim3, block: crate::interp::Dim3, spec: Vec<Sp>, expect_ok: bool) { case_entry(dir, name, k, &k.name, grid, block, spec, expect_ok) }
// the same, for a kernel whose PTX entry point has another name (a code generation variant of the same IR)
fn case_entry(dir: &str, name: &str, k: &Kernel, entry: &str, grid: crate::interp::Dim3, block: crate::interp::Dim3, spec: Vec<Sp>, expect_ok: bool) {
    // LC_SMALL=1 leaves out the big cases (keeps the exported suite small when disk space is short)
    if std::env::var("LC_SMALL").is_ok() && spec.iter().map(|s| if let Sp::B(v) = s { v.len() } else { 0 }).sum::<usize>() > 400_000 { return; }
    let d = format!("{}/cases/{}", dir, name); fs::create_dir_all(&d).unwrap();
    let (r, outs) = run_on(false, k, grid, block, &spec); assert_eq!(r.is_ok(), expect_ok, "interpreter result for {}", name);
    let mut meta = format!("kernel {}\ngrid {} {} {}\nblock {} {} {}\nexpect {}\n", entry, grid.x, grid.y, grid.z, block.x, block.y, block.z, if expect_ok { "ok" } else { "error" });
    let mut bi = 0;
    for s in &spec { match s { Sp::B(v) => { fs::write(format!("{}/b{}_in.bin", d, bi), bytes(v)).unwrap(); fs::write(format!("{}/b{}_exp.bin", d, bi), bytes(&outs[bi])).unwrap(); meta += &format!("arg buf b{} {}\n", bi, v.len()); bi += 1; } Sp::I(v) => meta += &format!("arg i32 {}\n", v) } }
    fs::write(format!("{}/meta.txt", d), meta).unwrap();
}

pub fn export(dir: &str) {
    fs::create_dir_all(format!("{}/ptx", dir)).unwrap();
    let (kv, km, kr, kb, ko, kg, kf) = (crate::vec_add(), crate::matmul_tiled(), crate::block_reduce(), crate::barrier_divergence(), crate::out_of_range(), crate::matmul_reg(), crate::matmul_fma());
    let (k4, k8) = (crate::matmul_fma4(), crate::matmul_fma8()); let v3 = [(crate::matmul_fma8db(), 128usize, 128usize), (crate::matmul_fma8x4(), 128, 64), (crate::matmul_fma8x4db(), 128, 64), (crate::matmul_fma8k32(), 128, 128)];
    for k in [&kv, &km, &kr, &kb, &ko, &kg, &kf, &k4, &k8] { fs::write(format!("{}/ptx/{}.ptx", dir, k.name), crate::ptx::to_ptx(k)).unwrap(); }
    for (k, _, _) in v3.iter() { fs::write(format!("{}/ptx/{}.ptx", dir, k.name), crate::ptx::to_ptx(k)).unwrap(); }
    for &n in &[1usize, 255, 256, 1000, 100003] { case(dir, &format!("vec_add_{}", n), &kv, dim((n + 255) / 256, 1, 1), dim(256, 1, 1), vec![Sp::B(crate::rnd(n, 1)), Sp::B(crate::rnd(n, 2)), Sp::B(vec![0f32; n]), Sp::I(n as i32)], true); }
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (64, 64, 64), (100, 50, 70), (33, 129, 17), (128, 128, 128)] {
        case(dir, &format!("matmul_{}x{}x{}", m, k, n), &km, dim((n + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); }
    for &n in &[1usize, 256, 1000, 12345, 65537] { let nb = (n + 255) / 256; case(dir, &format!("block_reduce_{}", n), &kr, dim(nb, 1, 1), dim(256, 1, 1), vec![Sp::B(crate::rnd(n, 5)), Sp::B(vec![0f32; nb]), Sp::I(n as i32)], true); }
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (64, 64, 64), (100, 50, 70), (33, 129, 17), (128, 128, 128), (65, 17, 130), (1, 16, 64)] {
        case(dir, &format!("matmulreg_{}x{}x{}", m, k, n), &kg, dim((n + 63) / 64, (m + 63) / 64, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); }
    for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (100, 50, 70), (128, 128, 128), (65, 17, 130)] {
        case(dir, &format!("matmulfma_{}x{}x{}", m, k, n), &kf, dim((n + 63) / 64, (m + 63) / 64, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); }
    for (kk, bt, tag) in [(&k4, 64usize, "matmulfma4"), (&k8, 128usize, "matmulfma8")] { for &(m, k, n) in &[(1usize, 768usize, 2304usize), (17, 33, 45), (100, 50, 70), (128, 128, 128), (65, 17, 130)] {
        case(dir, &format!("{}_{}x{}x{}", tag, m, k, n), kk, dim((n + bt - 1) / bt, (m + bt - 1) / bt, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); } }
    for (kk, bm, bn) in v3.iter() { for &(m, k, n) in &[(17usize, 33usize, 45usize), (100, 50, 70), (128, 128, 128), (65, 17, 130), (130, 70, 200), (3, 300, 190)] {
        case(dir, &format!("{}_{}x{}x{}", kk.name.replace("matmul_", "mm"), m, k, n), kk, dim((n + bn - 1) / bn, (m + bm - 1) / bm, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); } }
    // step 4d (bar Q7): code generation variants of the three best matmul kernels: check mode x full unrolling of the k loop
    for (kk, bm, bn) in [(&v3[2].0, 128usize, 64usize), (&v3[0].0, 128, 128), (&v3[1].0, 128, 64)] {
        for (chk, cn) in [(crate::ptx::Checks::Full, "full"), (crate::ptx::Checks::Cheap, "cheap"), (crate::ptx::Checks::None, "none")] { for unroll in [false, true] {
            if chk == crate::ptx::Checks::Full && !unroll { continue; }
            let suffix = format!("_{}{}", cn, if unroll { "_u" } else { "" }); let src = if unroll { crate::opt::optimise_with(kk, 40000) } else { kk.clone() };
            let entry = format!("{}{}", kk.name, suffix); fs::write(format!("{}/ptx/{}.ptx", dir, entry), crate::ptx::to_ptx_opts(&src, chk, false, &suffix)).unwrap();
            for &(m, k, n) in &[(100usize, 50usize, 70usize), (128, 128, 128), (65, 17, 130)] {
                case_entry(dir, &format!("{}_{}x{}x{}", entry.replace("matmul_", "v"), m, k, n), kk, &entry, dim((n + bn - 1) / bn, (m + bm - 1) / bm, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); }
        } }
    }
    // step 4d (bar Q8): the same kernels with the range analysis on (shared-memory checks proved away), full and cheap global checks, with and without unrolling
    for (kk, bm, bn) in [(&v3[2].0, 128usize, 64usize), (&v3[0].0, 128, 128), (&v3[1].0, 128, 64)] {
        for (chk, cn) in [(crate::ptx::Checks::Full, "full"), (crate::ptx::Checks::Cheap, "cheap")] { for unroll in [false, true] {
            let suffix = format!("_{}_p{}", cn, if unroll { "_u" } else { "" }); let src = if unroll { crate::opt::optimise_with(kk, 40000) } else { kk.clone() };
            let entry = format!("{}{}", kk.name, suffix); fs::write(format!("{}/ptx/{}.ptx", dir, entry), crate::ptx::to_ptx_opts(&src, chk, true, &suffix)).unwrap();
            for &(m, k, n) in &[(100usize, 50usize, 70usize), (128, 128, 128), (65, 17, 130)] {
                case_entry(dir, &format!("{}_{}x{}x{}", entry.replace("matmul_", "v"), m, k, n), kk, &entry, dim((n + bn - 1) / bn, (m + bm - 1) / bm, 1), dim(16, 16, 1), vec![Sp::B(crate::rnd(m * k, 3)), Sp::B(crate::rnd(k * n, 4)), Sp::B(vec![0f32; m * n]), Sp::I(m as i32), Sp::I(k as i32), Sp::I(n as i32)], true); }
        } }
    }
    // shared-memory out-of-range kernel (index = thread id + 1 on an array exactly as long as the block): the analysis must NOT prove it, so the access is still reported
    { let ks = crate::shared_oob(); for (chk, cn) in [(crate::ptx::Checks::Full, "full"), (crate::ptx::Checks::Cheap, "cheap")] { let suffix = format!("_{}_p", cn); let entry = format!("{}{}", ks.name, suffix);
        fs::write(format!("{}/ptx/{}.ptx", dir, entry), crate::ptx::to_ptx_opts(&ks, chk, true, &suffix)).unwrap();
        case_entry(dir, &format!("negative_{}", entry), &ks, &entry, dim(1, 1, 1), dim(16, 1, 1), vec![Sp::B(vec![0f32; 16])], false); } }
    // out-of-range tests for the cheap check mode (a load and a store)
    { let (kl, ks) = (crate::out_of_range(), crate::out_of_range_store());
      for (chk, cn) in [(crate::ptx::Checks::Full, "full"), (crate::ptx::Checks::Cheap, "cheap")] {
        for kk in [&kl, &ks] { let suffix = format!("_{}", cn); let entry = format!("{}{}", kk.name, suffix); fs::write(format!("{}/ptx/{}.ptx", dir, entry), crate::ptx::to_ptx_opts(kk, chk, false, &suffix)).unwrap();
            case_entry(dir, &format!("negative_{}", entry), kk, &entry, dim(1, 1, 1), dim(1, 1, 1), vec![Sp::B(vec![0f32; 8]), Sp::I(8)], false); } } }
    case(dir, "negative_out_of_range", &ko, dim(1, 1, 1), dim(1, 1, 1), vec![Sp::B(vec![0f32; 8]), Sp::I(8)], false);
    println!("wrote PTX for many kernels and cases to {}", dir);
}
