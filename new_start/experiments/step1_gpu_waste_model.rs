// 30 Oct 2026, MODEL (trace-driven simulation of memory traffic and lane utilisation; NOT a measurement of any GPU). New start, charter step 1:
// on irregular kernels, how much of a GPU-style machine's work and memory traffic is waste?  Standard library only. Build: rustc -O -C target-cpu=native step1_gpu_waste_model.rs
// Kernels: level-synchronous breadth-first search (BFS, one thread per frontier vertex) and sparse matrix-vector product (SpMV, CSR, one thread per row) on generated graphs: skewed (R-MAT a=.57 b=.19 c=.19) and uniform random of the same size and mean degree.
// GPU-style model (assumptions, editable below): 32-lane warps in lock step; the unit of memory transfer is a 32-byte sector; a sector cache (L2) of L2_MB (default 2), 16-way LRU, write-allocate; 4-byte elements.
// Reported: (1) lane utilisation = useful lane-slots / issued lane-slots, for the naive thread-per-vertex mapping and for the warp-per-vertex mapping that good libraries use;
// (2) waste = DRAM bytes moved by the cache model / IDEAL bytes, where ideal = every distinct 4-byte word the kernel touches, moved exactly once (a fine-grain machine with unlimited on-chip capacity; capacity is NOT modelled and is the other half of the question).
// Pass bar of the charter: waste >= 5 or lane utilisation < 20% on a skewed graph (stated for the better, warp-per-vertex mapping as well, since the naive mapping is a strawman).
use std::time::Instant;
const SECTOR: u64 = 32; const WAYS: usize = 16;
struct Rng(u64);
impl Rng { fn next(&mut self) -> u64 { let mut x = self.0; x ^= x >> 12; x ^= x << 25; x ^= x >> 27; self.0 = x; x.wrapping_mul(0x2545F4914F6CDD1D) } fn f(&mut self) -> f64 { (self.next() >> 11) as f64 / (1u64 << 53) as f64 } }
fn rmat(scale: u32, ef: usize, seed: u64) -> (usize, Vec<u32>, Vec<u32>) {
    let n = 1usize << scale; let m = n * ef; let mut r = Rng(seed * 2654435761 + 88172645463325252); let (a, b, c) = (0.57, 0.19, 0.19); let mut s = Vec::with_capacity(m); let mut d = Vec::with_capacity(m);
    for _ in 0..m { let (mut u, mut v) = (0u32, 0u32); for bit in 0..scale { let x = r.f(); if x >= a + b { u |= 1 << bit; } if (x >= a && x < a + b) || x >= a + b + c { v |= 1 << bit; } } s.push(u); d.push(v); }
    (n, s, d)
}
fn uniform(scale: u32, ef: usize, seed: u64) -> (usize, Vec<u32>, Vec<u32>) {
    let n = 1usize << scale; let m = n * ef; let mut r = Rng(seed * 2654435761 + 88172645463325252); let mut s = Vec::with_capacity(m); let mut d = Vec::with_capacity(m);
    for _ in 0..m { s.push((r.next() % n as u64) as u32); d.push((r.next() % n as u64) as u32); } (n, s, d)
}
fn csr(n: usize, s: &[u32], d: &[u32]) -> (Vec<u32>, Vec<u32>) {
    let mut rp = vec![0u32; n + 1]; for i in 0..s.len() { rp[s[i] as usize + 1] += 1; rp[d[i] as usize + 1] += 1; } for i in 0..n { rp[i + 1] += rp[i]; }
    let mut pos: Vec<u32> = rp[..n].to_vec(); let mut col = vec![0u32; 2 * s.len()];
    for i in 0..s.len() { let (u, v) = (s[i] as usize, d[i] as usize); col[pos[u] as usize] = v as u32; pos[u] += 1; col[pos[v] as usize] = u as u32; pos[v] += 1; } (rp, col)
}
struct Cache { nsets: u64, tags: Vec<i64>, stamp: Vec<u64>, clock: u64, misses: u64, seen: Vec<u8> }
impl Cache {
    fn new(mb: f64, words: usize) -> Cache { let nsets = (mb * 1024.0 * 1024.0) as u64 / (SECTOR * WAYS as u64); Cache { nsets, tags: vec![-1; nsets as usize * WAYS], stamp: vec![0; nsets as usize * WAYS], clock: 0, misses: 0, seen: vec![0; words] } }
    #[inline] fn touch(&mut self, addr: u64) {
        self.seen[(addr >> 2) as usize] = 1; self.clock += 1; let line = addr >> 5; let set = (line % self.nsets) as usize; let tg = (line / self.nsets) as i64; let base = set * WAYS; let mut old = 0; let mut oldest = u64::MAX;
        for w in 0..WAYS { if self.tags[base + w] == tg { self.stamp[base + w] = self.clock; return; } if self.stamp[base + w] < oldest { oldest = self.stamp[base + w]; old = w; } }
        self.tags[base + old] = tg; self.stamp[base + old] = self.clock; self.misses += 1;
    }
    fn unique_bytes(&self) -> u64 { self.seen.iter().map(|&x| x as u64).sum::<u64>() * 4 }
}
// returns (used lane-slots, issued lane-slots, misses, unique bytes)
fn bfs(rp: &[u32], col: &[u32], n: usize, root: usize, mb: f64, shuf: bool) -> (u64, u64, u64, u64) {
    let mut rng = Rng(0x9E3779B97F4A7C15);
    let m = col.len() as u64; let nn = n as u64; let bc = 4 * (nn + 1); let bl = bc + 4 * m; let bf = bl + 4 * nn; let bn = bf + 4 * nn; let mut c = Cache::new(mb, (bn / 4 + nn + 8) as usize);
    let mut lvl = vec![-1i32; n]; let mut fr: Vec<u32> = vec![root as u32]; let mut nx: Vec<u32> = Vec::new(); lvl[root] = 0; let mut d = 0; let (mut used, mut issued) = (0u64, 0u64);
    while !fr.is_empty() {
        nx.clear(); if shuf { for i in (1..fr.len()).rev() { let j = (rng.next() % (i as u64 + 1)) as usize; fr.swap(i, j); } }
        for g in (0..fr.len()).step_by(32) {
            let hi = (g + 32).min(fr.len()); let mut mx = 0u64;
            for i in g..hi {
                let u = fr[i] as usize; let deg = (rp[u + 1] - rp[u]) as u64; used += deg; if deg > mx { mx = deg; }
                c.touch(bf + 4 * i as u64); c.touch(4 * u as u64); c.touch(4 * (u as u64 + 1));
                for e in rp[u]..rp[u + 1] { let v = col[e as usize] as usize; c.touch(bc + 4 * e as u64); c.touch(bl + 4 * v as u64); if lvl[v] < 0 { lvl[v] = d + 1; c.touch(bn + 4 * nx.len() as u64); nx.push(v as u32); } }
            }
            issued += 32 * mx;
        }
        std::mem::swap(&mut fr, &mut nx); d += 1;
    }
    (used, issued, c.misses, c.unique_bytes())
}
fn spmv(rp: &[u32], col: &[u32], n: usize, mb: f64, shuf: bool) -> (u64, u64, u64, u64) {
    let mut perm: Vec<u32> = (0..n as u32).collect(); if shuf { let mut rng = Rng(0x9E3779B97F4A7C15); for i in (1..n).rev() { let j = (rng.next() % (i as u64 + 1)) as usize; perm.swap(i, j); } }
    let m = col.len() as u64; let nn = n as u64; let bc = 4 * (nn + 1); let bv = bc + 4 * m; let bx = bv + 4 * m; let by = bx + 4 * nn; let mut c = Cache::new(mb, (by / 4 + nn + 8) as usize); let (mut used, mut issued) = (0u64, 0u64);
    for g in (0..n).step_by(32) {
        let hi = (g + 32).min(n); let mut mx = 0u64;
        for ii in g..hi {
            let i = perm[ii] as usize; let deg = (rp[i + 1] - rp[i]) as u64; used += deg; if deg > mx { mx = deg; }
            c.touch(4 * i as u64); c.touch(4 * (i as u64 + 1)); c.touch(by + 4 * i as u64);
            for e in rp[i]..rp[i + 1] { let v = col[e as usize] as u64; c.touch(bc + 4 * e as u64); c.touch(bv + 4 * e as u64); c.touch(bx + 4 * v); }
        }
        issued += 32 * mx;
    }
    (used, issued, c.misses, c.unique_bytes())
}
fn vector_util(rp: &[u32]) -> f64 { let (mut used, mut issued) = (0f64, 0f64); for i in 0..rp.len() - 1 { let d = (rp[i + 1] - rp[i]) as f64; if d > 0.0 { used += d; issued += 32.0 * (d / 32.0).ceil(); } } used / issued }
fn main() {
    let a: Vec<String> = std::env::args().collect(); let l2: f64 = a.get(1).map(|x| x.parse().unwrap()).unwrap_or(2.0); let maxs: u32 = a.get(2).map(|x| x.parse().unwrap()).unwrap_or(20);
    println!("GPU-style model: 32-lane warps, {}-byte sectors, L2 {} MB 16-way LRU (and 64 MB for comparison), 4-byte elements. MODEL, not a measurement.", SECTOR, l2);
    println!("[shuffled] = the same at 2 MB with the vertices processed in random order, the worst case for cache locality (a real GPU interleaves thousands of threads; the in-order figure is generous to the GPU, the shuffled one is a ceiling).");
    println!("waste = DRAM bytes moved by the sector-cache model / IDEAL bytes (each distinct 4-byte word touched, moved once). Lane utilisation: thread-per-vertex (naive) / warp-per-vertex (good libraries).\n");
    println!("{:<8} {:<3} {:<10} {:<8} | {:<19} | {:<26} | {:<26} | {}", "graph", "n", "edges(x2)", "max deg", "lane util naive/vec", "BFS waste @2MB [shuffled] / @64MB", "SpMV waste @2MB [shuffled] / @64MB", "footprint BFS / SpMV (MB)");
    let t0 = Instant::now();
    for (name, f) in [("skewed", rmat as fn(u32, usize, u64) -> (usize, Vec<u32>, Vec<u32>)), ("uniform", uniform as fn(u32, usize, u64) -> (usize, Vec<u32>, Vec<u32>))] {
        let mut scale = 16; while scale <= maxs {
            let (n, s, d) = f(scale, 16, scale as u64); let (rp, col) = csr(n, &s, &d); drop(s); drop(d); let mut root = 0; let mut best = 0; for i in 0..n { let dg = rp[i + 1] - rp[i]; if dg > best { best = dg; root = i; } }
            let (u1, i1, m1, q1) = bfs(&rp, &col, n, root, l2, false); let (_, _, m1b, _) = bfs(&rp, &col, n, root, 64.0, false); let (u2, i2, m2, q2) = spmv(&rp, &col, n, l2, false); let (_, _, m2b, _) = spmv(&rp, &col, n, 64.0, false);
            let (_, _, m1s, _) = bfs(&rp, &col, n, root, l2, true); let (_, _, m2s, _) = spmv(&rp, &col, n, l2, true);
            println!("{:<8} {:<3} {:<10} {:<8} | {:>5.1}% / {:>5.1}%     | {:>5.2}x [{:>5.2}x] / {:>5.2}x | {:>5.2}x [{:>5.2}x] / {:>5.2}x | {:.0} / {:.0}   [{:.0}s]", name, scale, col.len(), best, 100.0 * u2 as f64 / i2 as f64, 100.0 * vector_util(&rp),
                (m1 * SECTOR) as f64 / q1 as f64, (m1s * SECTOR) as f64 / q1 as f64, (m1b * SECTOR) as f64 / q1 as f64, (m2 * SECTOR) as f64 / q2 as f64, (m2s * SECTOR) as f64 / q2 as f64, (m2b * SECTOR) as f64 / q2 as f64, q1 as f64 / 1e6, q2 as f64 / 1e6, t0.elapsed().as_secs_f64()); let _ = (u1, i1);
            scale += 2;
        }
    }
}
