// Layer 1 and 3 of a CUDA-like stack, first version (2 Nov 2026): the programming model (kernels, grid, blocks, thread indices) and a runtime (device buffers, copies, launch) executing on CPU threads.
// Rust, standard library only. Build: rustc --edition 2021 -O minicuda.rs -o /tmp/minicuda ; run: /tmp/minicuda
// A kernel is a function run once per thread with its own indices, exactly as in CUDA. The next layer (compiler) will turn the same kernels into PTX for a real GPU; this layer is the contract those kernels are written against.
use std::sync::Arc;
use std::time::Instant;

#[derive(Clone, Copy, Debug)] pub struct Dim3 { pub x: usize, pub y: usize, pub z: usize }
pub fn dim(x: usize, y: usize, z: usize) -> Dim3 { Dim3 { x, y, z } }
#[derive(Clone, Copy)] pub struct Thread { pub block_idx: Dim3, pub thread_idx: Dim3, pub block_dim: Dim3, pub grid_dim: Dim3 }
impl Thread { pub fn global_x(&self) -> usize { self.block_idx.x * self.block_dim.x + self.thread_idx.x } pub fn global_y(&self) -> usize { self.block_idx.y * self.block_dim.y + self.thread_idx.y } }

// device memory: a raw buffer that kernels read and write from many threads (as on a GPU, the programmer keeps writes disjoint)
#[derive(Clone)] pub struct DevBuf { ptr: *mut f32, len: usize, _own: Arc<Vec<f32>> }
unsafe impl Send for DevBuf {} unsafe impl Sync for DevBuf {}
pub struct Device;
impl Device {
    pub fn alloc(len: usize) -> DevBuf { let mut v = Arc::new(vec![0f32; len]); let ptr = Arc::get_mut(&mut v).unwrap().as_mut_ptr(); DevBuf { ptr, len, _own: v } }
    pub fn copy_to_device(host: &[f32]) -> DevBuf { let b = Device::alloc(host.len()); unsafe { std::ptr::copy_nonoverlapping(host.as_ptr(), b.ptr, host.len()); } b }
    pub fn copy_to_host(b: &DevBuf) -> Vec<f32> { unsafe { std::slice::from_raw_parts(b.ptr, b.len).to_vec() } }
}
impl DevBuf { #[inline] pub fn get(&self, i: usize) -> f32 { debug_assert!(i < self.len); unsafe { *self.ptr.add(i) } } #[inline] pub fn set(&self, i: usize, v: f32) { debug_assert!(i < self.len); unsafe { *self.ptr.add(i) = v; } } }

// launch: run `kernel` once for every thread of every block; blocks are spread over the machine's cores, threads of one block run one after another (no shared memory or barriers in this first version)
pub fn launch<F: Fn(Thread) + Sync>(grid: Dim3, block: Dim3, kernel: F) {
    let nblocks = grid.x * grid.y * grid.z; let nworkers = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1).min(nblocks.max(1));
    let next = std::sync::atomic::AtomicUsize::new(0);
    std::thread::scope(|s| { for _ in 0..nworkers { s.spawn(|| loop {
        let b = next.fetch_add(1, std::sync::atomic::Ordering::Relaxed); if b >= nblocks { break; }
        let bi = dim(b % grid.x, (b / grid.x) % grid.y, b / (grid.x * grid.y));
        for tz in 0..block.z { for ty in 0..block.y { for tx in 0..block.x { kernel(Thread { block_idx: bi, thread_idx: dim(tx, ty, tz), block_dim: block, grid_dim: grid }); } } }
    }); } });
}

// ---- example kernels, written the way CUDA kernels are written ----
fn vec_add(t: Thread, a: &DevBuf, b: &DevBuf, c: &DevBuf, n: usize) { let i = t.global_x(); if i < n { c.set(i, a.get(i) + b.get(i)); } }
// C[m,n] = A[m,k] @ B[k,n], one thread per output element
fn matmul(t: Thread, a: &DevBuf, b: &DevBuf, c: &DevBuf, m: usize, k: usize, n: usize) {
    let (col, row) = (t.global_x(), t.global_y()); if row < m && col < n { let mut s = 0f32; for kk in 0..k { s += a.get(row * k + kk) * b.get(kk * n + col); } c.set(row * n + col, s); }
}

fn main() {
    println!("mini CUDA-like runtime on the CPU: {} worker threads", std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1));
    // vector add: 1,000,000 elements, blocks of 256 threads
    let n = 1_000_000usize; let ha: Vec<f32> = (0..n).map(|i| i as f32 * 0.5).collect(); let hb: Vec<f32> = (0..n).map(|i| 1.0 + (i % 7) as f32).collect();
    let (a, b, c) = (Device::copy_to_device(&ha), Device::copy_to_device(&hb), Device::alloc(n)); let t0 = Instant::now();
    launch(dim((n + 255) / 256, 1, 1), dim(256, 1, 1), |t| vec_add(t, &a, &b, &c, n)); let dt = t0.elapsed();
    let hc = Device::copy_to_host(&c); let err = (0..n).map(|i| (hc[i] - (ha[i] + hb[i])).abs()).fold(0f32, f32::max);
    println!("vec_add  n={}: max error {:.1e}, {:.2} ms", n, err, dt.as_secs_f64() * 1e3);
    // matrix multiply: several shapes, 16 x 16 thread blocks, against a plain CPU reference
    for &(m, k, nn) in &[(1usize, 768usize, 2304usize), (64, 768, 768), (128, 512, 256), (257, 100, 191), (512, 512, 512)] {
        let ha: Vec<f32> = (0..m * k).map(|i| ((i * 31 % 17) as f32 - 8.0) / 8.0).collect(); let hb: Vec<f32> = (0..k * nn).map(|i| ((i * 13 % 11) as f32 - 5.0) / 8.0).collect();
        let (a, b, c) = (Device::copy_to_device(&ha), Device::copy_to_device(&hb), Device::alloc(m * nn)); let t0 = Instant::now();
        launch(dim((nn + 15) / 16, (m + 15) / 16, 1), dim(16, 16, 1), |t| matmul(t, &a, &b, &c, m, k, nn)); let dt = t0.elapsed(); let hc = Device::copy_to_host(&c);
        let mut maxrel = 0f32; for i in 0..m { for j in 0..nn { let mut s = 0f32; for kk in 0..k { s += ha[i * k + kk] * hb[kk * nn + j]; } let e = (hc[i * nn + j] - s).abs() / s.abs().max(1.0); if e > maxrel { maxrel = e; } } }
        println!("matmul {:>3}x{:>3}x{:>3}: max relative error {:.1e}, {:.2} ms, {:.2} GFLOP/s", m, k, nn, maxrel, dt.as_secs_f64() * 1e3, 2.0 * (m * k * nn) as f64 / dt.as_secs_f64() / 1e9);
    }
}
